"""
Embedding service implementation using Korean-specialized models
"""

import logging
import torch
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer

from .models import EmbeddingResult, VectorResult, EmbeddingHealth

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Korean text embedding service"""

    def __init__(self):
        self.models: Dict[str, SentenceTransformer] = {}
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.available_models = {
            "ko-sbert": "jhgan/ko-sroberta-multitask",
            "bge-m3-korean": "BAAI/bge-m3",
            "ko-sentence-bert": "snunlp/KR-SBERT-V40K-klueNLI-augSTS"
        }
        self.default_model = "ko-sbert"

        logger.info(f"EmbeddingService initialized on device: {self.device}")

    def load_model(self, model_name: str = None) -> bool:
        """Load embedding model"""
        model_name = model_name or self.default_model

        if model_name in self.models:
            logger.info(f"Model {model_name} already loaded")
            return True

        if model_name not in self.available_models:
            raise ValueError(f"Model {model_name} not available. Available models: {list(self.available_models.keys())}")

        try:
            model_path = self.available_models[model_name]
            logger.info(f"Loading model: {model_path}")

            model = SentenceTransformer(model_path, device=self.device)
            self.models[model_name] = model

            logger.info(f"Model {model_name} loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise

    def get_embedding(self, text: str, model_name: str = None) -> np.ndarray:
        """Get embedding for text"""
        model_name = model_name or self.default_model

        if model_name not in self.models:
            self.load_model(model_name)

        try:
            model = self.models[model_name]
            embedding = model.encode(text, convert_to_numpy=True)
            return embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    def get_batch_embeddings(self, texts: List[str], model_name: str = None) -> np.ndarray:
        """Get embeddings for multiple texts"""
        model_name = model_name or self.default_model

        if model_name not in self.models:
            self.load_model(model_name)

        try:
            model = self.models[model_name]
            embeddings = model.encode(texts, convert_to_numpy=True)
            return embeddings

        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise

    def create_job_vector(self, company_info: str, required_skills: str, model_name: str = None) -> VectorResult:
        """
        Create job vector: [company_info_vector || required_skills_vector]
        Returns: VectorResult object
        """
        try:
            model_name = model_name or self.default_model

            # Get individual embeddings
            general_vector = self.get_embedding(company_info, model_name)
            skills_vector = self.get_embedding(required_skills, model_name)

            # Combine vectors
            combined_vector = np.concatenate([general_vector, skills_vector])
            dimension = self.get_embedding_dimension(model_name)

            logger.info(f"Job vector created - General: {general_vector.shape}, Skills: {skills_vector.shape}, Combined: {combined_vector.shape}")

            return VectorResult(
                general_vector=general_vector.tolist(),
                skills_vector=skills_vector.tolist(),
                combined_vector=combined_vector.tolist(),
                model=model_name,
                dimension=dimension
            )

        except Exception as e:
            logger.error(f"Failed to create job vector: {e}")
            raise

    def create_applicant_vector(self, preferences: str, skills: str, model_name: str = None) -> VectorResult:
        """
        Create applicant vector: [preferences_vector || skills_vector]
        Returns: VectorResult object
        """
        try:
            model_name = model_name or self.default_model

            # Get individual embeddings
            general_vector = self.get_embedding(preferences, model_name)
            skills_vector = self.get_embedding(skills, model_name)

            # Combine vectors
            combined_vector = np.concatenate([general_vector, skills_vector])
            dimension = self.get_embedding_dimension(model_name)

            logger.info(f"Applicant vector created - General: {general_vector.shape}, Skills: {skills_vector.shape}, Combined: {combined_vector.shape}")

            return VectorResult(
                general_vector=general_vector.tolist(),
                skills_vector=skills_vector.tolist(),
                combined_vector=combined_vector.tolist(),
                model=model_name,
                dimension=dimension
            )

        except Exception as e:
            logger.error(f"Failed to create applicant vector: {e}")
            raise

    def health_check(self) -> EmbeddingHealth:
        """Check service health"""
        model_status = {}
        for model_name in self.available_models.keys():
            model_status[model_name] = model_name in self.models

        service_status = "healthy" if any(model_status.values()) else "no_models_loaded"

        return EmbeddingHealth(
            service_status=service_status,
            available_models=list(self.available_models.keys()),
            model_status=model_status,
            device=self.device
        )

    def get_embedding_dimension(self, model_name: str = None) -> int:
        """Get embedding dimension for model"""
        model_name = model_name or self.default_model

        if model_name not in self.models:
            self.load_model(model_name)

        # Test with a simple text to get dimension
        test_embedding = self.get_embedding("test", model_name)
        return test_embedding.shape[0]


# Global service instance
embedding_service = EmbeddingService()


def get_embedding_service() -> EmbeddingService:
    """Get global embedding service instance"""
    return embedding_service