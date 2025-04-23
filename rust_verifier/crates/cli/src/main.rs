fn main() {
    let counts = vec![10, 5, 3, 0];
    let proof = histogram_zkp::prove(&counts, &counts);
    assert!(histogram_zkp::verify(&proof));
    println!("OK");
}
