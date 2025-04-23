use ark_ec::PairingEngine;                          // 0.4 系ではこのパス
use ark_ff::PrimeField;
use ark_poly::univariate::DensePolynomial;         // 0.4 系 API
use ark_poly::UVPolynomial;
use ark_poly_commit::kzg10::{KZG10, Powers, Proof, VerifierKey};
use rand::rngs::OsRng;
use serde::{Deserialize, Serialize};
use serde_json::json;

/// 証明用パラメータ
#[derive(Serialize, Deserialize)]
pub struct HistProof {
    pub vk: Vec<u8>,
    pub comm: Vec<u8>,
    pub proof: Vec<u8>,
    pub r_hex: String,
    pub val_hex: String,
}

/// ヒストグラム一致 ZKP を生成
pub fn prove<E: PairingEngine>(counts: &[u64]) -> anyhow::Result<HistProof> {
    // 多項式差分 p(x) = Σ counts[i] * x^i - v
    let coeffs: Vec<_> = counts.iter().map(|&c| E::Fr::from(c)).collect();
    let poly = DensePolynomial::from_coefficients_vec(coeffs.clone());         // UVPolynomial トレイトが in scope
    let max_deg = poly.degree();                                              // degree メソッドも UVPolynomial
    let mut rng = OsRng;

    // trusted setup
    let srs = KZG10::<E, DensePolynomial<E::Fr>>::setup(max_deg, false, &mut rng)?;  
    let (powers, vk) = srs.trim(max_deg).unwrap();                             // 0.4 系では trim(&srs,deg)
    // commit
    let (comm, rand) = KZG10::commit(&powers, &poly, None, Some(&mut rng))?;    // Option<&mut RngCore>
    // open (private)
    let proof: Proof<E> = KZG10::open(&powers, &poly, poly.evaluate(&E::Fr::from(1u8)), &rand)?;
    // シリアライズ
    let mut vk_bytes = vec![];
    vk.serialize_compressed(&mut vk_bytes)?;
    let mut comm_bytes = vec![];
    comm.serialize_compressed(&mut comm_bytes)?;
    let mut proof_bytes = vec![];
    proof.serialize_compressed(&mut proof_bytes)?;

    Ok(HistProof {
        vk: vk_bytes,
        comm: comm_bytes,
        proof: proof_bytes,
        r_hex: hex::encode(poly.evaluate(&E::Fr::from(1u8)).into_repr().to_bytes_be()),
        val_hex: hex::encode(poly.evaluate(&E::Fr::from(1u8)).into_repr().to_bytes_be()),
    })
}

/// ZKP を検証
pub fn verify<E: PairingEngine>(p: &HistProof) -> anyhow::Result<()> {
    // デシリアライズ
    let vk = VerifierKey::<E>::deserialize_compressed(&*p.vk)?;
    let comm = <_ as Commitment>::deserialize_compressed(&*p.comm)?;
    let proof = Proof::<E>::deserialize_compressed(&*p.proof)?;
    // 返り値チェック
    let ok = KZG10::check(&vk, &comm, &[], &proof, Some(&mut OsRng))?;
    anyhow::ensure!(ok, "Histogram consistency proof failed");
    Ok(())
}
