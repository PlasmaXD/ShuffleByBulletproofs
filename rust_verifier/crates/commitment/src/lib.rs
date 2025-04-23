use bulletproofs::{BulletproofGens, PedersenGens};
use curve25519_dalek_ng::ristretto::{CompressedRistretto, RistrettoPoint};
use curve25519_dalek_ng::scalar::Scalar;
use merlin::Transcript;
use rand::rngs::OsRng;
use std::iter::Sum;
use std::fs;
use std::env;
use serde::{Serialize, Deserialize};
use serde_json::{Value, json};

#[derive(Serialize, Deserialize)]
struct ShuffleInput {
    reports: Vec<Value>,
    commitments: Vec<String>,
    permutation: Vec<usize>,
}

#[derive(Serialize, Deserialize)]
struct VerifyInput {
    original_commitments: Vec<String>,
    shuffled_commitments: Vec<String>,
    proofs: Value,
}

fn main() {
    let args: Vec<String> = env::args().collect();
    
    if args.len() < 3 {
        eprintln!("Usage: {} <command> <input_file>", args[0]);
        std::process::exit(1);
    }
    
    let command = &args[1];
    let input_file = &args[2];
    
    match command.as_str() {
        "commit"  => generate_commitments(input_file),
        "shuffle" => shuffle_commitments(input_file),
        "verify"  => verify_shuffle(input_file),
        _ => {
            eprintln!("Unknown command: {}", command);
            std::process::exit(1);
        }
    }
}

fn generate_commitments(input_file: &str) {
    // ファイルからレポートを読み込む
    let file_content = fs::read_to_string(input_file)
        .expect("Failed to read input file");
    
    let reports: Vec<Value> = serde_json::from_str(&file_content)
        .expect("Failed to parse reports");
    
    let pc_gens = PedersenGens::default();
    let mut rng = OsRng;
    let mut commitments = Vec::new();
    
    // 各レポートに対してコミットメントを生成
    for report in reports {
        let report_str = serde_json::to_string(&report).expect("Failed to serialize report");
        let report_hash = blake3::hash(report_str.as_bytes());
        let mut hash_bytes = [0u8; 32];
        hash_bytes.copy_from_slice(&report_hash.as_bytes()[..32]);
        let report_value = Scalar::from_bytes_mod_order(hash_bytes);
        
        let blinding = Scalar::from_bytes_mod_order_wide(&rng.gen::<[u8; 64]>());
        let commitment = pc_gens.commit(report_value, blinding).compress();
        
        commitments.push(hex::encode(commitment.as_bytes()));
    }
    
    // JSON形式で出力
    println!("{}", serde_json::to_string(&commitments).expect("Failed to serialize commitments"));
}

fn shuffle_commitments(input_file: &str) {
    // ファイルから入力を読み込む
    let file_content = fs::read_to_string(input_file)
        .expect("Failed to read input file");
    
    let input: ShuffleInput = serde_json::from_str(&file_content)
        .expect("Failed to parse input");
    
    // コミットメントをデコード
    let original_commitments: Vec<CompressedRistretto> = input.commitments.iter()
        .map(|hex| {
            let bytes = hex::decode(hex).expect("Failed to decode commitment");
            CompressedRistretto::from_slice(&bytes)
        })
        .collect();
    
    // シャッフル前の合計を計算
    let sum_before: RistrettoPoint = original_commitments.iter()
        .map(|c| c.decompress().expect("Failed to decompress"))
        .sum();
    
    // 順列に従ってコミットメントをシャッフル
    let shuffled_commitments: Vec<CompressedRistretto> = input.permutation.iter()
        .map(|&i| original_commitments[i])
        .collect();
    
    // シャッフル後の合計を計算
    let sum_after: RistrettoPoint = shuffled_commitments.iter()
        .map(|c| c.decompress().expect("Failed to decompress"))
        .sum();
    
    // 証明を生成
    let proof = json!({
        "sum_before": hex::encode(sum_before.compress().as_bytes()),
        "sum_after":  hex::encode(sum_after.compress().as_bytes()),
        "permutation": input.permutation
    });
    
    // シャッフルされたコミットメントをエンコード
    let shuffled_commitments_hex: Vec<String> = shuffled_commitments.iter()
        .map(|c| hex::encode(c.as_bytes()))
        .collect();
    
    // 結果をJSON形式で出力
    let result = json!({
        "shuffled_commitments": shuffled_commitments_hex,
        "proofs": proof
    });
    
    println!("{}", serde_json::to_string(&result).expect("Failed to serialize result"));
}

fn verify_shuffle(input_file: &str) {
    // ファイルから入力を読み込む
    let file_content = fs::read_to_string(input_file)
        .expect("Failed to read input file");
    
    let input: VerifyInput = serde_json::from_str(&file_content)
        .expect("Failed to parse input");
    
    // オリジナルのコミットメントをデコード
    let original_commitments: Vec<CompressedRistretto> = input.original_commitments.iter()
        .map(|hex| {
            let bytes = hex::decode(hex).expect("Failed to decode original commitment");
            CompressedRistretto::from_slice(&bytes)
        })
        .collect();
    
    // シャッフルされたコミットメントをデコード
    let shuffled_commitments: Vec<CompressedRistretto> = input.shuffled_commitments.iter()
        .map(|hex| {
            let bytes = hex::decode(hex).expect("Failed to decode shuffled commitment");
            CompressedRistretto::from_slice(&bytes)
        })
        .collect();
    
    // 合計を再計算
    let recalculated_sum_before: RistrettoPoint = original_commitments.iter()
        .map(|c| c.decompress().expect("Failed to decompress"))
        .sum();
    
    let recalculated_sum_after: RistrettoPoint = shuffled_commitments.iter()
        .map(|c| c.decompress().expect("Failed to decompress"))
        .sum();
    
    // 証明から合計を取得
    let proof_sum_before_hex = input.proofs["sum_before"].as_str().expect("Invalid proof format");
    let proof_sum_after_hex  = input.proofs["sum_after"].as_str().expect("Invalid proof format");
    
    let proof_sum_before = CompressedRistretto::from_slice(&hex::decode(proof_sum_before_hex).unwrap())
        .decompress().expect("Failed to decompress proof sum before");
    let proof_sum_after  = CompressedRistretto::from_slice(&hex::decode(proof_sum_after_hex).unwrap())
        .decompress().expect("Failed to decompress proof sum after");
    
    // 検証
    let valid_sums = recalculated_sum_before == proof_sum_before
                  && recalculated_sum_after  == proof_sum_after
                  && recalculated_sum_before == recalculated_sum_after;
    
    if valid_sums {
        println!("Verification successful");
        std::process::exit(0);
    } else {
        eprintln!("Verification failed");
        std::process::exit(1);
    }
}
