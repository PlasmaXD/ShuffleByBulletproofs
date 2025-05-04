# verifiable_shuffler.py
import subprocess
import json
import os
import tempfile
import hashlib
import base64
import random
import numpy as np
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes

class VerifiableShuffler:
    """
    ゼロ知識証明を用いて検証可能なシャッフル操作を実装するクラス
    簡略版の実装（教育目的）と、Rust実装の呼び出しの両方をサポート
    """
    
    def __init__(self, use_rust_implementation=False):
        """
        初期化
        
        Args:
            use_rust_implementation: Rustの実装を使用するかどうか
        """
        self.use_rust_implementation = use_rust_implementation
        self.commitments = []
        self.shuffled_commitments = []
        self.permutation = []
        self.proofs = []
        # self.rust_binary_path = os.path.join(os.path.dirname(__file__), "shuffle_verifier")
        # self.rust_binary_path = os.path.join(
        # os.path.dirname(os.path.abspath(__file__)), 
        # "rust_verifier/target/release/shuffle_verifier")    
        # Rust 実装バイナリのパスを Debug/Release から自動選択
        base = os.path.dirname(os.path.abspath(__file__))
        release = os.path.join(base, "../rust_verifier/target/release/shuffle_verifier")
        debug   = os.path.join(base, "../rust_verifier/target/debug/shuffle_verifier")
        # release = os.path.join(base, "../rust_verifier2/target/release/rust_verifier2")
        # debug   = os.path.join(base, "../rust_verifier2/target/debug/rust_verifier2")
        if os.path.exists(release):
            self.rust_binary_path = release
        elif os.path.exists(debug):
            self.rust_binary_path = debug
        else:
            # ビルドされていなければフォールバックで Python 実装を強制
            self.use_rust_implementation = False
            self.rust_binary_path = None
        
    def commit_reports(self, reports):
        """
        レポートのリストに対するコミットメントを生成
        
        Args:
            reports: コミットするレポートのリスト
            
        Returns:
            コミットメントのリスト
        """
        self.commitments = []
        
        if self.use_rust_implementation:
            # レポートをファイルに書き込む
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                json.dump(reports, f)
                temp_file = f.name
            
            # Rustバイナリを呼び出してコミットメントを生成
            result = subprocess.run(
                [self.rust_binary_path, "commit", temp_file],
                capture_output=True, text=True
            )
            
            # 一時ファイルを削除
            os.unlink(temp_file)
            
            # 結果を解析
            if result.returncode != 0:
                raise RuntimeError(f"Commitment generation failed: {result.stderr}")
            
            self.commitments = json.loads(result.stdout)
            return self.commitments
        else:
            # Pythonによる簡略化された実装
            for report in reports:
                # レポートの文字列表現を計算
                report_str = json.dumps(report, sort_keys=True)
                
                # SHA-256ハッシュを計算
                h = hashlib.sha256(report_str.encode()).digest()
                
                # ランダムなブラインディング値を生成
                blinding = os.urandom(32)
                
                # ハッシュとブラインディングを組み合わせてコミットメント生成
                commitment = hashlib.sha256(h + blinding).hexdigest()
                
                # コミットメントとブラインディングを保存
                self.commitments.append({
                    'commitment': commitment,
                    'blinding': base64.b64encode(blinding).decode(),
                    'report_hash': base64.b64encode(h).decode()
                })
            
            return [c['commitment'] for c in self.commitments]
    
    def shuffle_commitments(self, reports):
        """
        レポートとそのコミットメントをシャッフルし、証明を生成
        
        Args:
            reports: シャッフルするレポートのリスト
            
        Returns:
            シャッフルされたレポートのリスト
        """
        if len(self.commitments) != len(reports):
            self.commit_reports(reports)
        
        # 順列を生成
        n = len(reports)
        self.permutation = list(range(n))
        random.shuffle(self.permutation)
        
        # レポートをシャッフル
        shuffled_reports = [reports[self.permutation[i]] for i in range(n)]
        
        if self.use_rust_implementation:
            # レポートとコミットメントをファイルに書き込む
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                json.dump({
                    'reports': reports,
                    'commitments': self.commitments,
                    'permutation': self.permutation
                }, f)
                temp_file = f.name
            
            # Rustバイナリを呼び出して証明を生成
            result = subprocess.run(
                [self.rust_binary_path, "shuffle", temp_file],
                capture_output=True, text=True
            )
            
            # 一時ファイルを削除
            os.unlink(temp_file)
            
            # 結果を解析
            if result.returncode != 0:
                raise RuntimeError(f"Shuffle proof generation failed: {result.stderr}")
            
            result_data = json.loads(result.stdout)
            self.shuffled_commitments = result_data['shuffled_commitments']
            self.proofs = result_data['proofs']
        else:
            # Pythonによる簡略化された実装
            # シャッフルされたコミットメントを生成
            self.shuffled_commitments = [self.commitments[self.permutation[i]] for i in range(n)]
            
            # 簡略化された証明を生成（実際のゼロ知識証明ではない）
            self.proofs = {
                'permutation': self.permutation,
                'sum_hash_before': self._compute_sum_hash([c['commitment'] for c in self.commitments]),
                'sum_hash_after': self._compute_sum_hash([c['commitment'] for c in self.shuffled_commitments])
            }
        
        return shuffled_reports
    
    def verify_shuffle(self):
        """
        シャッフルの証明を検証
        
        Returns:
            検証結果（真偽値）
        """
        if not self.proofs:
            return False
        
        if self.use_rust_implementation:
            # 証明と元のコミットメントをファイルに書き込む
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                json.dump({
                    'original_commitments': self.commitments,
                    'shuffled_commitments': self.shuffled_commitments,
                    'proofs': self.proofs
                }, f)
                temp_file = f.name
            
            # Rustバイナリを呼び出して証明を検証
            result = subprocess.run(
                [self.rust_binary_path, "verify", temp_file],
                capture_output=True, text=True
            )
            
            # 一時ファイルを削除
            os.unlink(temp_file)
            
            # 結果を解析
            return result.returncode == 0
        else:
            # 簡略化された検証（実際のゼロ知識検証ではない）
            sum_hash_before = self._compute_sum_hash([c['commitment'] for c in self.commitments])
            sum_hash_after = self._compute_sum_hash([c['commitment'] for c in self.shuffled_commitments])
            
            return sum_hash_before == sum_hash_after and sum_hash_before == self.proofs['sum_hash_before']
    
    def _compute_sum_hash(self, commitments):
        """
        コミットメントの合計ハッシュを計算
        
        Args:
            commitments: コミットメントのリスト
            
        Returns:
            合計ハッシュ
        """
        combined = ''.join(sorted(commitments))
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def get_verification_data(self):
        """
        検証データを取得
        
        Returns:
            検証に必要なデータ
        """
        return {
            'original_commitment_count': len(self.commitments),
            'shuffled_commitment_count': len(self.shuffled_commitments),
            'proofs': self.proofs
        }
