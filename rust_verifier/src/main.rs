// src/main.rs
use ark_bls12_381::{Fr, G1Projective as G1};
use ark_ec::ProjectiveCurve;
use ark_ff::{One, UniformRand, Zero};
use ark_poly::{
    univariate::DensePolynomial, 
    Polynomial, UVPolynomial,
};
use ark_serialize::{CanonicalDeserialize, CanonicalSerialize};
// use std::io::Cursor;
use ark_std::io::Cursor;
use rand::rngs::OsRng;
use serde::{Deserialize, Serialize};
use std::env;
use std::fs;
use std::ops::{Div, Mul, Sub};
use ark_ff::PrimeField;
// use ark_std::io::Cursor;
use ark_ec::AffineCurve;

// KZG10多項式コミットメント用の構造体
struct KZG10 {
    powers_of_g: Vec<G1>,
    powers_of_h: Vec<G1>,
    g: G1,
    h: G1,
}

impl KZG10 {
    // 信頼できるセットアップ
    fn setup(max_degree: usize, rng: &mut OsRng) -> Self {
        let g = G1::rand(rng);
        let h = G1::rand(rng);
        let s = Fr::rand(rng);
        
        let mut powers_of_g = Vec::with_capacity(max_degree + 1);
        let mut powers_of_h = Vec::with_capacity(max_degree + 1);
        
        let mut s_power = Fr::one();
        for _ in 0..=max_degree {
            powers_of_g.push(g.mul(s_power.into_repr()));
            powers_of_h.push(h.mul(s_power.into_repr()));
            s_power *= s;
        }
        
        KZG10 {
            powers_of_g,
            powers_of_h,
            g,
            h,
        }
    }
    
    // 多項式へのコミットメント
    fn commit(&self, polynomial: &DensePolynomial<Fr>) -> G1 {
        let mut commitment = G1::zero();
        for (i, coeff) in polynomial.coeffs.iter().enumerate() {
            if i < self.powers_of_g.len() {
                commitment += self.powers_of_g[i].mul(&coeff.into_repr());
            }
        }
        commitment
    }
    
    // 評価証明の生成
    fn create_evaluation_proof(
        &self,
        polynomial: &DensePolynomial<Fr>,
        point: Fr,
        value: Fr,
    ) -> (G1, Fr) {
        // 多項式 q(X) = (p(X) - p(point)) / (X - point)
        let divisor = DensePolynomial::from_coefficients_vec(vec![-point, Fr::one()]);
        let mut quotient = polynomial.clone();
        quotient.coeffs[0] -= value;
        
        // 多項式の除算
        let quotient = quotient.div(&divisor);
        
        let proof = self.commit(&quotient);
        (proof, value)
    }
    
    // 評価証明の検証
    fn verify_evaluation(
        &self,
        commitment: G1,
        point: Fr,
        value: Fr,
        proof: G1,
    ) -> bool {
        let lhs = commitment - self.g.mul(value.into_repr());
        // Fix the problematic line
        let rhs = proof.mul(point.into_repr()) - self.powers_of_g[1].mul(proof.into_affine().into_projective().into_affine().x.into_repr());
        lhs == rhs
    }
    
}

#[derive(Serialize, Deserialize)]
struct HistogramInput {
    counts_in: Vec<u64>,
    counts_out: Vec<u64>,
}

#[derive(Serialize, Deserialize)]
struct HistProof {
    vk_bytes: Vec<u8>,
    comm_in_bytes: Vec<u8>,
    comm_out_bytes: Vec<u8>,
    proof_bytes: Vec<u8>,
    challenge_bytes: Vec<u8>,
    value_bytes: Vec<u8>,
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
        "prove" => prove_histogram(input_file),
        "verify" => verify_histogram(input_file),
        "commit" => generate_commitments(input_file),
        "shuffle" => shuffle_commitments(input_file),
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
    
    let reports: Vec<serde_json::Value> = serde_json::from_str(&file_content)
        .expect("Failed to parse reports");
    
    let pc_gens = bulletproofs::PedersenGens::default();
    let mut rng = OsRng;
    let mut commitments = Vec::new();
    
    // 各レポートに対してコミットメントを生成
    for report in reports {
        let report_str = serde_json::to_string(&report).expect("Failed to serialize report");
        let report_hash = blake3::hash(report_str.as_bytes());
        let report_value = curve25519_dalek_ng::scalar::Scalar::from(
            u64::from_le_bytes(report_hash.as_bytes()[0..8].try_into().unwrap())
        );
        
        let blinding = curve25519_dalek_ng::scalar::Scalar::random(&mut rng);
        let commitment = pc_gens.commit(report_value, blinding).compress();
        
        commitments.push(hex::encode(commitment.as_bytes()));
    }
    
    // JSON形式で出力
    println!("{}", serde_json::to_string(&commitments).expect("Failed to serialize commitments"));
}

#[derive(Serialize, Deserialize)]
struct ShuffleInput {
    reports: Vec<serde_json::Value>,
    commitments: Vec<String>,
    permutation: Vec<usize>,
}

fn shuffle_commitments(input_file: &str) {
    // ファイルから入力を読み込む
    let file_content = fs::read_to_string(input_file)
        .expect("Failed to read input file");
    
    let input: ShuffleInput = serde_json::from_str(&file_content)
        .expect("Failed to parse input");
    
    // コミットメントをデコード
    let mut original_commitments = Vec::new();
    for commitment_hex in &input.commitments {
        let bytes = hex::decode(commitment_hex).expect("Failed to decode commitment");
        let compressed = curve25519_dalek_ng::ristretto::CompressedRistretto::from_slice(&bytes);
        original_commitments.push(compressed);
    }
    
    // シャッフル前の合計を計算
    let sum_before: curve25519_dalek_ng::ristretto::RistrettoPoint = original_commitments.iter()
        .map(|c| c.decompress().expect("Failed to decompress"))
        .sum();
    
    // 順列に従ってコミットメントをシャッフル
    let shuffled_commitments: Vec<curve25519_dalek_ng::ristretto::CompressedRistretto> = input.permutation.iter()
        .map(|&i| original_commitments[i])
        .collect();
    
    // シャッフル後の合計を計算
    let sum_after: curve25519_dalek_ng::ristretto::RistrettoPoint = shuffled_commitments.iter()
        .map(|c| c.decompress().expect("Failed to decompress"))
        .sum();
    
    // 証明を生成
    let proof = serde_json::json!({
        "sum_before": hex::encode(sum_before.compress().as_bytes()),
        "sum_after": hex::encode(sum_after.compress().as_bytes()),
        "permutation": input.permutation
    });
    
    // シャッフルされたコミットメントをエンコード
    let shuffled_commitments_hex: Vec<String> = shuffled_commitments.iter()
        .map(|c| hex::encode(c.as_bytes()))
        .collect();
    
    // 結果をJSON形式で出力
    let result = serde_json::json!({
        "shuffled_commitments": shuffled_commitments_hex,
        "proofs": proof
    });
    
    println!("{}", serde_json::to_string(&result).expect("Failed to serialize result"));
}

#[derive(Serialize, Deserialize)]
struct VerifyInput {
    original_commitments: Vec<String>,
    shuffled_commitments: Vec<String>,
    proofs: serde_json::Value,
}

fn verify_shuffle(input_file: &str) {
    // ファイルから入力を読み込む
    let file_content = fs::read_to_string(input_file)
        .expect("Failed to read input file");
    
    let input: VerifyInput = serde_json::from_str(&file_content)
        .expect("Failed to parse input");
    
    // オリジナルのコミットメントをデコード
    let original_commitments: Vec<curve25519_dalek_ng::ristretto::CompressedRistretto> = input.original_commitments.iter()
        .map(|hex| {
            let bytes = hex::decode(hex).expect("Failed to decode original commitment");
            curve25519_dalek_ng::ristretto::CompressedRistretto::from_slice(&bytes)
        })
        .collect();
    
    // シャッフルされたコミットメントをデコード
    let shuffled_commitments: Vec<curve25519_dalek_ng::ristretto::CompressedRistretto> = input.shuffled_commitments.iter()
        .map(|hex| {
            let bytes = hex::decode(hex).expect("Failed to decode shuffled commitment");
            curve25519_dalek_ng::ristretto::CompressedRistretto::from_slice(&bytes)
        })
        .collect();
    
    // 合計を再計算
    let recalculated_sum_before: curve25519_dalek_ng::ristretto::RistrettoPoint = original_commitments.iter()
        .map(|c| c.decompress().expect("Failed to decompress"))
        .sum();
    
    let recalculated_sum_after: curve25519_dalek_ng::ristretto::RistrettoPoint = shuffled_commitments.iter()
        .map(|c| c.decompress().expect("Failed to decompress"))
        .sum();
    
    // 証明から合計を取得
    let proof_sum_before_hex = input.proofs["sum_before"].as_str().expect("Invalid proof format");
    let proof_sum_after_hex = input.proofs["sum_after"].as_str().expect("Invalid proof format");
    
    let proof_sum_before_bytes = hex::decode(proof_sum_before_hex).expect("Failed to decode proof sum before");
    let proof_sum_after_bytes = hex::decode(proof_sum_after_hex).expect("Failed to decode proof sum after");
    
    let proof_sum_before = curve25519_dalek_ng::ristretto::CompressedRistretto::from_slice(&proof_sum_before_bytes)
        .decompress().expect("Failed to decompress proof sum before");
        
    let proof_sum_after = curve25519_dalek_ng::ristretto::CompressedRistretto::from_slice(&proof_sum_after_bytes)
        .decompress().expect("Failed to decompress proof sum after");
    
    // 検証
    let valid_sums = recalculated_sum_before == proof_sum_before && 
                    recalculated_sum_after == proof_sum_after && 
                    recalculated_sum_before == recalculated_sum_after;
    
    if valid_sums {
        // 検証成功
        println!("Verification successful");
        std::process::exit(0);
    } else {
        // 検証失敗
        eprintln!("Verification failed");
        std::process::exit(1);
    }
}

fn prove_histogram(input_file: &str) {
    // ファイルから入力を読み込む
    let file_content = fs::read_to_string(input_file)
        .expect("Failed to read input file");
    
    let input: HistogramInput = serde_json::from_str(&file_content)
        .expect("Failed to parse input");
    
    let mut rng = OsRng;
    
    // 多項式の次数を決定
    let max_degree = std::cmp::max(input.counts_in.len(), input.counts_out.len());
    
    // KZG10セットアップ
    let kzg = KZG10::setup(max_degree, &mut rng);
    
    // 入力ヒストグラムから多項式を作成
    let poly_in = create_multiset_polynomial(&input.counts_in);
    
    // 出力ヒストグラムから多項式を作成
    let poly_out = create_multiset_polynomial(&input.counts_out);
    
    // 多項式へのコミットメント
    let comm_in = kzg.commit(&poly_in);
    let comm_out = kzg.commit(&poly_out);
    
    // ランダムな評価点を生成
    let challenge = Fr::rand(&mut rng);
    
    // 評価値を計算
    let value_in = poly_in.evaluate(&challenge);
    let value_out = poly_out.evaluate(&challenge);
    
    // 評価値が等しいことを確認
    assert_eq!(value_in, value_out, "Histograms do not match!");
    
    // 評価証明を生成
    let (proof, _) = kzg.create_evaluation_proof(&poly_in, challenge, value_in);
    
    // シリアライズ
    let mut vk_bytes = Vec::new();
    kzg.g.serialize(&mut vk_bytes).unwrap();
    kzg.h.serialize(&mut vk_bytes).unwrap();
    for power in &kzg.powers_of_g[0..2] {
        power.serialize(&mut vk_bytes).unwrap();
    }
    
    let mut comm_in_bytes = Vec::new();
    comm_in.serialize(&mut comm_in_bytes).unwrap();
    
    let mut comm_out_bytes = Vec::new();
    comm_out.serialize(&mut comm_out_bytes).unwrap();
    
    let mut proof_bytes = Vec::new();
    proof.serialize(&mut proof_bytes).unwrap();
    
    let mut challenge_bytes = Vec::new();
    challenge.serialize(&mut challenge_bytes).unwrap();
    
    let mut value_bytes = Vec::new();
    value_in.serialize(&mut value_bytes).unwrap();
    
    // 証明を作成
    let hist_proof = HistProof {
        vk_bytes,
        comm_in_bytes,
        comm_out_bytes,
        proof_bytes,
        challenge_bytes,
        value_bytes,
    };
    
    // 結果を出力
    println!("{}", serde_json::to_string(&hist_proof).expect("Failed to serialize proof"));
}

fn verify_histogram(input_file: &str) {
    // ファイルから証明を読み込む
    let file_content = fs::read_to_string(input_file)
        .expect("Failed to read input file");
    
    let proof: HistProof = serde_json::from_str(&file_content)
        .expect("Failed to parse proof");
    
    // デシリアライズ
    let g1_size = 96; // BLS12-381のG1要素のシリアル化サイズ
    
    // let g = G1::deserialize(&mut Cursor::new(&proof.vk_bytes[0..g1_size])).unwrap();
    // let h = G1::deserialize(&mut Cursor::new(&proof.vk_bytes[g1_size..2*g1_size])).unwrap();
    // let g = G1::deserialize(&mut Cursor::new(&proof.vk_bytes[0..g1_size])).unwrap();
    // let h = G1::deserialize(&mut Cursor::new(&proof.vk_bytes[g1_size..2*g1_size])).unwrap();
    let g = G1::deserialize(&proof.vk_bytes[0..g1_size]).unwrap();
    let h = G1::deserialize(&proof.vk_bytes[g1_size..2*g1_size]).unwrap();
    let mut powers_of_g = Vec::new();
    let offset = 2 * g1_size;
    powers_of_g.push(G1::deserialize(&proof.vk_bytes[offset..offset+g1_size]).unwrap());
    powers_of_g.push(G1::deserialize(&proof.vk_bytes[offset+g1_size..offset+2*g1_size]).unwrap());
    let kzg = KZG10 {
        powers_of_g,
        powers_of_h: Vec::new(), // 検証には不要
        g,
        h,
    };
    
    // In verify_histogram function
    let comm_in = G1::deserialize(&*proof.comm_in_bytes).unwrap();
    let comm_out = G1::deserialize(&*proof.comm_out_bytes).unwrap();
    let proof_point = G1::deserialize(&*proof.proof_bytes).unwrap();
    let challenge = Fr::deserialize(&*proof.challenge_bytes).unwrap();
    let value = Fr::deserialize(&*proof.value_bytes).unwrap();

    // コミットメントが等しいか確認
    let commitments_equal = comm_in == comm_out;
    
    // 評価証明を検証
    let proof_valid = kzg.verify_evaluation(comm_in, challenge, value, proof_point);
    
    if commitments_equal && proof_valid {
        println!("Verification successful");
        std::process::exit(0);
    } else {
        eprintln!("Verification failed");
        if !commitments_equal {
            eprintln!("Commitments are not equal");
        }
        if !proof_valid {
            eprintln!("Evaluation proof is invalid");
        }
        std::process::exit(1);
    }
}

// 多重集合から多項式を作成する関数
fn create_multiset_polynomial(counts: &[u64]) -> DensePolynomial<Fr> {
    // 多重集合の要素を展開
    let mut elements = Vec::new();
    for (value, &count) in counts.iter().enumerate() {
        for _ in 0..count {
            elements.push(Fr::from(value as u64));
        }
    }
    
    // 多項式 P(X) = ∏(X - elements[i]) を作成
    let mut poly = DensePolynomial::from_coefficients_vec(vec![Fr::one()]);
    
    for element in elements {
        let factor = DensePolynomial::from_coefficients_vec(vec![-element, Fr::one()]);
        poly = poly.mul(&factor);
    }
    
    poly
}
