// Cargo.toml の依存関係例:
// [dependencies]
// bulletproofs = "4.0.0"
// curve25519-dalek-ng = "4.1.1"
// merlin = "3.0"
// rand = "0.8"

use bulletproofs::{BulletproofGens, PedersenGens};
use curve25519_dalek_ng::ristretto::{CompressedRistretto, RistrettoPoint};
use curve25519_dalek_ng::scalar::Scalar;
use merlin::Transcript;
use rand::rngs::OsRng;
use rand::seq::SliceRandom;
use std::iter::Sum;

fn main() {
    // 例として、3つの値のコミットメントを生成
    let values = vec![100u64, 200u64, 300u64];
    let bp_gens = BulletproofGens::new(64, values.len());
    let pc_gens = PedersenGens::default();

    let mut rng = OsRng;
    let mut commitments: Vec<CompressedRistretto> = vec![];

    // 各値に対してランダムなブラインディングを用いてコミットメントを作成
    for &v in values.iter() {
        let blinding: Scalar = Scalar::random(&mut rng);
        let commitment = pc_gens.commit(Scalar::from(v), blinding).compress();
        commitments.push(commitment);
    }

    // シャッフル前の合計コミットメントを計算（各コミットメントは加法的であるため、合計が保存される）
    let sum_original: RistrettoPoint = commitments.iter()
        .map(|c| c.decompress().expect("decompress failed"))
        .sum();

    // コミットメントをランダムな順序でシャッフルする
    let (shuffled, permutation) = shuffle_commitments(&commitments, &mut rng);

    // シャッフル後の合計コミットメントを計算
    let sum_shuffled: RistrettoPoint = shuffled.iter()
        .map(|c| c.decompress().expect("decompress failed"))
        .sum();

    println!("Original sum: {:?}", sum_original.compress());
    println!("Shuffled sum: {:?}", sum_shuffled.compress());

    if sum_original == sum_shuffled {
        println!("合計コミットメントが一致しました！");
    } else {
        println!("合計コミットメントが一致しません！");
    }

    println!("適用された順序（Permutation）: {:?}", permutation);
}

// コミットメントをシャッフルし、その順序（Permutation）を返す関数
fn shuffle_commitments<R: rand::Rng>(
    commitments: &Vec<CompressedRistretto>,
    rng: &mut R,
) -> (Vec<CompressedRistretto>, Vec<usize>) {
    let mut indices: Vec<usize> = (0..commitments.len()).collect();
    indices.shuffle(rng);
    let shuffled = indices.iter().map(|&i| commitments[i]).collect();
    (shuffled, indices)
}

// RistrettoPoint は std::iter::Sum を実装しているので、sum() が利用できます。
