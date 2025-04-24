use std::fs;
use std::process::{Command, exit};
use serde_json::{Value, json};

fn main() {
    println!("=== 差分プライバシーZKPパイプライン実行 ===");
    
    // 1. コミットメント生成
    println!("\n1. コミットメント生成中...");
    let commit_output = Command::new("cargo")
        .args(&["run", "--", "commit", "input_reports.json"])
        .output()
        .expect("コミットメント生成に失敗しました");
    
    if !commit_output.status.success() {
        eprintln!("コミットメント生成エラー: {}", String::from_utf8_lossy(&commit_output.stderr));
        exit(1);
    }
    
    let commitments: Vec<String> = serde_json::from_str(
        &String::from_utf8_lossy(&commit_output.stdout)
    ).expect("コミットメント出力のパースに失敗しました");
    
    println!("生成されたコミットメント: {:?}", commitments);
    
    // 2. シャッフル入力ファイル作成
    println!("\n2. シャッフル入力ファイル作成中...");
    let shuffle_input = json!({
        "reports": [
            {
                "user_id": "user1",
                "timestamp": "2025-04-24T03:41:00Z",
                "data": "sample_data_1"
            },
            {
                "user_id": "user2",
                "timestamp": "2025-04-24T03:41:00Z",
                "data": "sample_data_2"
            }
        ],
        "commitments": commitments,
        "permutation": [1, 0]
    });
    
    fs::write("shuffle_input.json", 
        serde_json::to_string_pretty(&shuffle_input).unwrap()
    ).expect("シャッフル入力ファイルの作成に失敗しました");
    
    // 3. シャッフル実行
    println!("\n3. シャッフル実行中...");
    let shuffle_output = Command::new("cargo")
        .args(&["run", "--", "shuffle", "shuffle_input.json"])
        .output()
        .expect("シャッフル実行に失敗しました");
    
    if !shuffle_output.status.success() {
        eprintln!("シャッフルエラー: {}", String::from_utf8_lossy(&shuffle_output.stderr));
        exit(1);
    }
    
    let shuffle_result: Value = serde_json::from_str(
        &String::from_utf8_lossy(&shuffle_output.stdout)
    ).expect("シャッフル出力のパースに失敗しました");
    
    println!("シャッフル結果: {}", serde_json::to_string_pretty(&shuffle_result).unwrap());
    
    // 4. 検証入力ファイル作成
    println!("\n4. 検証入力ファイル作成中...");
    let verification_input = json!({
        "original_commitments": commitments,
        "shuffled_commitments": shuffle_result["shuffled_commitments"],
        "proofs": shuffle_result["proofs"]
    });
    
    fs::write("verification_input.json", 
        serde_json::to_string_pretty(&verification_input).unwrap()
    ).expect("検証入力ファイルの作成に失敗しました");
    
    // 5. 検証実行
    println!("\n5. 検証実行中...");
    let verify_output = Command::new("cargo")
        .args(&["run", "--", "verify", "verification_input.json"])
        .output()
        .expect("検証実行に失敗しました");
    
    println!("検証結果: {}", String::from_utf8_lossy(&verify_output.stdout));
    if !verify_output.status.success() {
        eprintln!("検証エラー: {}", String::from_utf8_lossy(&verify_output.stderr));
        exit(1);
    }
    
    println!("\n=== 全プロセスが正常に完了しました ===");
}
