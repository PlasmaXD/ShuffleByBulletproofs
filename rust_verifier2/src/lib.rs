// src/lib.rs
use curve25519_dalek::ristretto::{CompressedRistretto, RistrettoPoint};
use curve25519_dalek::scalar::Scalar;

use rand::rngs::OsRng;
use rand::seq::SliceRandom;
use std::iter::Sum;

/// Sum Preservation シャッフル
pub fn shuffle_sum_preservation(mut commits: Vec<CompressedRistretto>, perm: &[usize]) -> (Vec<CompressedRistretto>, RistrettoPoint, RistrettoPoint) {
    let sum_before: RistrettoPoint = commits.iter().map(|c| c.decompress().unwrap()).sum();
    let mut shuffled = perm.iter().map(|&i| commits[i]).collect::<Vec<_>>();
    let sum_after: RistrettoPoint = shuffled.iter().map(|c| c.decompress().unwrap()).sum();
    (shuffled, sum_before, sum_after)
}

/// Permutation シャッフル
pub fn shuffle_permutation(mut commits: Vec<CompressedRistretto>, perm: &[usize]) -> Vec<CompressedRistretto> {
    perm.iter().map(|&i| commits[i]).collect()
}
