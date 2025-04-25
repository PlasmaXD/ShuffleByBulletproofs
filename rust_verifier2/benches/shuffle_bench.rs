// benches/shuffle_bench.rs

use criterion::{criterion_group, criterion_main, Criterion, BenchmarkId, Throughput};
use rust_verifier2::{shuffle_sum_preservation, shuffle_permutation};
use curve25519_dalek::ristretto::CompressedRistretto;
use curve25519_dalek::scalar::Scalar;
use curve25519_dalek::ristretto::RistrettoPoint;
use rand::rngs::OsRng;
use rand::RngCore;
use bulletproofs::PedersenGens;
use rand::prelude::SliceRandom;

// ベンチ用の入力を生成
fn generate_commits(n: usize) -> Vec<CompressedRistretto> {
    let mut rng = OsRng;
    (0..n).map(|_| {
        let v = Scalar::random(&mut rng);
        let r = Scalar::random(&mut rng);
        let pc = PedersenGens::default().commit(v, r);

        pc.compress()
    }).collect()
}

fn bench_shuffles(c: &mut Criterion) {
    let mut group = c.benchmark_group("shuffle");
    for &n in &[100, 1_000, 10_000] {
        let commits = generate_commits(n);
        let perm: Vec<usize> = {
            let mut p: Vec<usize> = (0..n).collect();
            p.shuffle(&mut OsRng);
            p
        };

        group.throughput(Throughput::Elements(n as u64));
        group.bench_with_input(BenchmarkId::new("sum_preservation", n), &(&commits, &perm), |b, (cmt, p)| {
            b.iter(|| { shuffle_sum_preservation(cmt.to_vec(), p); });
        });
        group.bench_with_input(BenchmarkId::new("permutation", n), &(&commits, &perm), |b, (cmt, p)| {
            b.iter(|| { shuffle_permutation(cmt.to_vec(), p); });
        });
    }
    group.finish();
}

criterion_group!(benches, bench_shuffles);
criterion_main!(benches);
