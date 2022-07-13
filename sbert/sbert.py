from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('snunlp/KR-SBERT-V40K-klueNLI-augSTS') 
sentences = ['잠이 옵니다', '졸음이 옵니다', '기차가 옵니다']
vectors = model.encode(sentences) # encode sentences into vectors
similarities = util.cos_sim(vectors, vectors) # compute similarity between sentence vectors
print(similarities)
