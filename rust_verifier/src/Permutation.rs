// src/main.rs
use bulletproofs::{BulletproofGens, PedersenGens};
use curve25519_dalek_ng::ristretto::{CompressedRistretto, RistrettoPoint};
use curve25519_dalek_ng::scalar::Scalar;
use merlin::Transcript;
use rand::rngs::OsRng;
use rand::seq::SliceRandom;
use std::iter::Sum;
use std::fs;
use std::env;
use serde::{Serialize, Deserialize};
use serde_json::{Value, json};

#[derive(Serialize, Deserialize)]
struct ShuffleInput {
    reports: Vec<Value>,
    commitments: Vec<String>,
    // ここを追加: "sum" または "permutation"
    proof_type: Option<String>,
}

#[derive(Serialize, Deserialize)]
struct VerifyInput {
    original_commitments: Vec<String>,
    shuffled_commitments: Vec<String>,
    proofs: Value,
    // ここを追加: "sum" または "permutation"
    proof_type: Option<String>,
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
        "commit"           => generate_commitments(input_file),
        "shuffle"          => shuffle_commitments(input_file),
        "verify"           => verify_shuffle(input_file),
        _ => {
            eprintln!("Unknown command: {}", command);
            std::process::exit(1);
        }
    }
}

fn generate_commitments(input_file: &str) {
    let file_content = fs::read_to_string(input_file).expect("Failed to read input file");
    let reports: Vec<Value> = serde_json::from_str(&file_content).expect("Failed to parse reports");
    let pc_gens = PedersenGens::default();
    let mut rng = OsRng;
    let mut commitments = Vec::new();

    for report in reports {
        let report_str = serde_json::to_string(&report).unwrap();
        let report_hash = blake3::hash(report_str.as_bytes());
        let report_value = Scalar::from(u64::from_le_bytes(report_hash.as_bytes()[0..8].try_into().unwrap()));
        let blinding = Scalar::random(&mut rng);
        let commitment = pc_gens.commit(report_value, blinding).compress();
        commitments.push(hex::encode(commitment.as_bytes()));
    }

    println!("{}", serde_json::to_string(&commitments).unwrap());
}

fn shuffle_commitments(input_file: &str) {
    let file_content = fs::read_to_string(input_file).expect("Failed to read input file");
    let mut input: ShuffleInput = serde_json::from_str(&file_content).expect("Failed to parse input");

    // デフォルトは sum（合計不変性証明）
    let proof_type = input.proof_type.take().unwrap_or_else(|| "sum".into());

    // コミットメントをデコード
    let mut original_commitments = input.commitments.iter().map(|hex| {
        let bytes = hex::decode(hex).unwrap();
        CompressedRistretto::from_slice(&bytes)
    }).collect::<Vec<_>>();

    // シャッフル
    // permutation が指定されていなければランダム生成
    let permutation = if input.reports.is_empty() {
        (0..original_commitments.len()).collect::<Vec<usize>>()
    } else {
        input.reports.iter().enumerate().map(|(i,_)| i).collect::<Vec<usize>>()
    };
    let mut perm = permutation.clone();
    perm.shuffle(&mut OsRng);

    let shuffled_commitments = perm.iter().map(|&i| original_commitments[i]).collect::<Vec<_>>();

    // 証明部分
    let proofs = match proof_type.as_str() {
        "permutation" => {
            // そのまま permutation ベクタを返す
            json!({ "permutation": perm })
        }
        _ => {
            // sum preservation proof
            let sum_before: RistrettoPoint = original_commitments.iter()
                .map(|c| c.decompress().unwrap()).sum();
            let sum_after: RistrettoPoint = shuffled_commitments.iter()
                .map(|c| c.decompress().unwrap()).sum();
            json!({
                "sum_before": hex::encode(sum_before.compress().as_bytes()),
                "sum_after":  hex::encode(sum_after.compress().as_bytes()),
            })
        }
    };

    // 出力コミットメントを hex 文字列に戻す
    let shuffled_hex = shuffled_commitments.iter()
        .map(|c| hex::encode(c.as_bytes())).collect::<Vec<_>>();

    // proof_type も一緒に出力
    let result = json!({
        "shuffled_commitments": shuffled_hex,
        "proofs": proofs,
        "proof_type": proof_type,
    });
    println!("{}", serde_json::to_string(&result).unwrap());
}

fn verify_shuffle(input_file: &str) {
    let file_content = fs::read_to_string(input_file).expect("Failed to read input file");
    let input: VerifyInput = serde_json::from_str(&file_content).expect("Failed to parse input");

    let proof_type = input.proof_type.unwrap_or_else(|| "sum".into());

    // デコード
    let orig = input.original_commitments.iter().map(|hex| {
        let bytes = hex::decode(hex).unwrap();
        CompressedRistretto::from_slice(&bytes)
    }).collect::<Vec<_>>();
    let shuf = input.shuffled_commitments.iter().map(|hex| {
        let bytes = hex::decode(hex).unwrap();
        CompressedRistretto::from_slice(&bytes)
    }).collect::<Vec<_>>();

    let valid = match proof_type.as_str() {
        "permutation" => {
            // permutation ベクタを取り出してチェック
            if let Some(perm) = input.proofs.get("permutation").and_then(Value::as_array) {
                perm.iter().enumerate().all(|(j, v)| {
                    let i = v.as_u64().unwrap() as usize;
                    shuf[j].decompress().unwrap() == orig[i].decompress().unwrap()
                })
            } else {
                false
            }
        }
        _ => {
            // sum preservation
            let rec_before: RistrettoPoint = orig.iter().map(|c| c.decompress().unwrap()).sum();
            let rec_after:  RistrettoPoint = shuf.iter().map(|c| c.decompress().unwrap()).sum();
            let pb = hex::decode(input.proofs["sum_before"].as_str().unwrap()).unwrap();
            let pa = hex::decode(input.proofs["sum_after" ].as_str().unwrap()).unwrap();
            let proof_before = CompressedRistretto::from_slice(&pb).decompress().unwrap();
            let proof_after  = CompressedRistretto::from_slice(&pa).decompress().unwrap();
            rec_before == proof_before && rec_after == proof_after && rec_before == rec_after
        }
    };

    if valid {
        println!("Verification successful");
        std::process::exit(0);
    } else {
        eprintln!("Verification failed");
        std::process::exit(1);
    }
}
