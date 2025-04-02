# verifiable_shuffler.py
import hashlib
import random
import json

class VerifiableShuffler:
    def __init__(self):
        self.input_reports = []
        self.output_reports = []
        self.permutation = []
        self.commitment = None
    
    def add_report(self, report):
        """レポートをバッファに追加"""
        self.input_reports.append(report)
    
    def shuffle(self):
        """レポートをシャッフルして証明を生成"""
        # 入力レポートのハッシュを計算
        input_hashes = [self._hash_report(r) for r in self.input_reports]
        
        # 順列を生成
        n = len(self.input_reports)
        self.permutation = list(range(n))
        random.shuffle(self.permutation)
        
        # 出力レポートを生成
        self.output_reports = [self.input_reports[self.permutation[i]] for i in range(n)]
        
        # コミットメントを生成（順列のハッシュ）
        perm_str = json.dumps(self.permutation)
        self.commitment = hashlib.sha256(perm_str.encode()).hexdigest()
        
        return self.output_reports, self.commitment
    
    def generate_proof(self, challenge_indices):
        """チャレンジに対する証明を生成"""
        proofs = []
        for i in challenge_indices:
            if i < len(self.permutation):
                original_index = self.permutation[i]
                proof = {
                    "output_index": i,
                    "input_index": original_index,
                    "input_hash": self._hash_report(self.input_reports[original_index]),
                    "output_hash": self._hash_report(self.output_reports[i])
                }
                proofs.append(proof)
        return proofs
    
    def _hash_report(self, report):
        """レポートのハッシュを計算"""
        report_str = json.dumps(report, sort_keys=True)
        return hashlib.sha256(report_str.encode()).hexdigest()

class ShuffleVerifier:
    def verify_shuffle(self, input_hashes, output_hashes, commitment, proofs):
        """シャッフルの証明を検証"""
        # 各証明を検証
        for proof in proofs:
            output_index = proof["output_index"]
            input_index = proof["input_index"]
            
            # 入力と出力のハッシュが一致するか確認
            if proof["input_hash"] != input_hashes[input_index]:
                return False
            if proof["output_hash"] != output_hashes[output_index]:
                return False
        
        return True
