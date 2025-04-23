// src/setup.rs
use rand::rngs::OsRng;
use ark_bls12_381::Bls12_381;
use ark_groth16::generate_random_parameters;
use std::fs;
use bincode;
use crate::circuit::ShuffleCircuit; // ← main.rs と同じ回路を再利用

pub fn run_setup(n_dummy: usize) {
    // ダミー入力で回路を作成
    let dummy = ShuffleCircuit {
        in_points: vec![],
        out_points: vec![],
    };
    let params = generate_random_parameters::<Bls12_381, _, _>(dummy, &mut OsRng).unwrap();

    fs::write("params.bin", bincode::serialize(&params).unwrap()).unwrap();
    fs::write("vk.bin", bincode::serialize(&params.vk).unwrap()).unwrap();

    println!("Setup done. params.bin / vk.bin を生成しました。");
}
