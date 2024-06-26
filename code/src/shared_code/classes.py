import torchhd, torch, torch.nn.functional as F
from typing import Any, List, Dict, Optional, Tuple, overload, Type
from functools import partial
from .helpers import similarity_func_partial

class Vocabulary:
    def __init__(self):
        self.word2idx: Dict[str, int]  = {}
        self.idx2word: List[str] = []

    def add_word(self, word:str):
        if word not in self.idx2word:
            self.idx2word.append(word)
            self.word2idx[word] = len(self.idx2word) - 1
        return self.word2idx[word]

    def __len__(self):
        return len(self.idx2word)
    
class Codebook():
    def __init__(self, dim:int = 10_000, vsa_type:str = 'MAP'):
        self.dim = dim
        self.vsa_type: str = vsa_type
        self.similarity_func = partial(similarity_func_partial, vsa_type)
        self.dictionary: Vocabulary = Vocabulary()
        self.vectors: List[torchhd.VSATensor] = []

    def add_value(self, value:str, vsa_vector:Optional[torchhd.VSATensor] = None) -> torchhd.VSATensor:
        r"""Add value to codebook
        Args:
          value: value to be added
          vsa_vector: vector representation of value; must be of same dimension as codebook
        Returns:
          Vector representation of value
        """
        if value not in self.dictionary.word2idx:
            self.dictionary.add_word(value)
            value_vector = vsa_vector if vsa_vector is not None else torchhd.random(1, self.dim, vsa=self.vsa_type)[0]
            self.vectors.append(value_vector)
        return self.vectors[self.dictionary.word2idx[value]]
    
    def most_similar_values(self, vector: torchhd.VSATensor, topk: int = 0) -> List[Tuple[torchhd.VSATensor, float]]:
        if topk == 0:
            topk = len(self.dictionary)
        vector_stack = torch.stack(self.vectors, dim=0)
        sim = self.similarity_func(vector, vector_stack)
        topk_sim, topk_idx = torch.topk(sim, topk)
        topk_values = [self.dictionary.idx2word[idx] for idx in topk_idx]
        return list(zip(topk_values, topk_sim.tolist())) #TODO: also return vectors? Or make user get them using getitem?

    def __len__(self):
        return len(self.dictionary)
    
    def __getitem__(self, key):
        try:
          if isinstance(key, int):
              return self.vectors[key]
          elif isinstance(key, str):
              return self.vectors[self.dictionary.word2idx[key]]
          else:
              raise TypeError("Invalid argument type")
        except (IndexError, KeyError):
          return None