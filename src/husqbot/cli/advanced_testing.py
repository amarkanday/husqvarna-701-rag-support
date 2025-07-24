"""
Advanced testing and evaluation for RAG system quality.
"""

import logging
import os
from typing import List, Dict, Any
from husqbot.core.rag_system import HusqvarnaRAGSystem
from husqbot.core.response_enhancement import ResponseEnhancer

logger = logging.getLogger(__name__)


class AdvancedQueryTester:
    """Advanced testing for RAG system quality assessment."""
    
    def __init__(self, project_id: str, location: str = "us-central1"):
        """Initialize the advanced tester.
        
        Args:
            project_id: Google Cloud project ID
            location: Google Cloud region
        """
        self.rag_system = HusqvarnaRAGSystem(project_id, location)
        self.enhancer = ResponseEnhancer()
        
        # Comprehensive test queries covering different aspects
        self.test_queries = {
            'maintenance': [
                "How do I check the oil level?",
                "What is the service interval for the air filter?",
                "How do I adjust the chain tension?",
                "When should I replace the spark plug?",
                "How do I check tire pressure?"
            ],
            'troubleshooting': [
                "My motorcycle won't start, what should I check?",
                "The engine is overheating, what could be wrong?",
                "I hear strange noises from the engine",
                "The bike is hard to shift gears",
                "Why is my fuel consumption high?"
            ],
            'safety': [
                "What safety precautions should I take when working on the engine?",
                "How do I safely check the cooling system?",
                "What are the dangers of electrical work?",
                "Safety procedures for brake maintenance",
                "Hot surface warnings during maintenance"
            ],
            'specifications': [
                "What is the engine oil capacity?",
                "What are the torque specifications for the cylinder head?",
                "What tire pressure should I use?",
                "What type of coolant does the bike use?",
                "What are the valve clearance specifications?"
            ],
            'procedures': [
                "How do I remove the front wheel?",
                "Step-by-step oil change procedure",
                "How to replace the air filter",
                "Brake pad replacement procedure",
                "How to check valve clearances"
            ]
        }
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive quality assessment across all query types.
        
        Returns:
            Detailed test results and quality metrics
        """
        results = {
            'overall_score': 0.0,
            'category_scores': {},
            'query_results': {},
            'system_stats': {},
            'recommendations': []
        }
        
        # Get system statistics
        results['system_stats'] = self.rag_system.get_system_stats()
        
        total_score = 0.0
        total_queries = 0
        
        # Test each category
        for category, queries in self.test_queries.items():
            category_scores = []
            category_results = []
            
            for query in queries:
                query_result = self._test_single_query(query, category)
                category_results.append(query_result)
                category_scores.append(query_result['quality_score'])
                total_score += query_result['quality_score']
                total_queries += 1
            
            results['category_scores'][category] = {
                'average_score': sum(category_scores) / len(category_scores),
                'query_count': len(queries),
                'results': category_results
            }
            results['query_results'][category] = category_results
        
        results['overall_score'] = total_score / total_queries
        
        # Generate recommendations
        results['recommendations'] = self._generate_recommendations(results)
        
        return results
    
    def _test_single_query(self, query: str, category: str) -> Dict[str, Any]:
        """Test a single query and assess quality.
        
        Args:
            query: Query to test
            category: Query category
            
        Returns:
            Detailed query test results
        """
        # Get RAG response
        rag_result = self.rag_system.query(query, top_k=5, similarity_threshold=0.6)
        
        # Enhance chunks for better analysis
        if rag_result['chunks_found'] > 0:
            enhanced_chunks = self.enhancer.enhance_chunk_context(
                rag_result.get('chunks', [])
            )
        else:
            enhanced_chunks = []
        
        # Validate response quality
        quality_assessment = self.enhancer.validate_response_quality(
            rag_result['response'], query, enhanced_chunks
        )
        
        # Category-specific scoring
        category_bonus = self._calculate_category_bonus(
            rag_result['response'], category, enhanced_chunks
        )
        
        final_score = quality_assessment['overall_score'] + category_bonus
        
        return {
            'query': query,
            'category': category,
            'success': rag_result['success'],
            'chunks_found': rag_result['chunks_found'],
            'fallback_mode': rag_result.get('fallback_mode', False),
            'response_length': len(rag_result['response']),
            'quality_score': min(final_score, 1.0),  # Cap at 1.0
            'quality_details': quality_assessment,
            'enhanced_chunks': len(enhanced_chunks),
            'response_preview': rag_result['response'][:200] + "..."
        }
    
    def _calculate_category_bonus(
        self, 
        response: str, 
        category: str, 
        chunks: List[Dict]
    ) -> float:
        """Calculate category-specific quality bonus.
        
        Args:
            response: Generated response
            category: Query category
            chunks: Source chunks
            
        Returns:
            Bonus score (0.0 to 0.2)
        """
        response_lower = response.lower()
        bonus = 0.0
        
        if category == 'maintenance':
            # Look for step-by-step instructions
            if any(word in response_lower for word in ['step', 'first', 'then', 'next']):
                bonus += 0.1
            # Look for tool mentions
            if any(word in response_lower for word in ['tool', 'wrench', 'socket']):
                bonus += 0.05
        
        elif category == 'safety':
            # Safety content should have prominent warnings
            safety_words = ['warning', 'danger', 'caution', 'safety']
            safety_count = sum(1 for word in safety_words if word in response_lower)
            bonus += min(safety_count * 0.05, 0.15)
        
        elif category == 'specifications':
            # Should include specific measurements
            if self.enhancer._has_technical_data(response):
                bonus += 0.1
            # Should reference manual sections
            if any(word in response_lower for word in ['page', 'section', 'manual']):
                bonus += 0.05
        
        elif category == 'troubleshooting':
            # Should provide diagnostic steps
            if any(word in response_lower for word in ['check', 'inspect', 'verify']):
                bonus += 0.08
            # Should mention possible causes
            if any(word in response_lower for word in ['cause', 'problem', 'issue']):
                bonus += 0.07
        
        elif category == 'procedures':
            # Should have structured format
            if self.enhancer._has_structured_content(response):
                bonus += 0.1
            # Should mention required conditions
            if any(word in response_lower for word in ['condition', 'require', 'before']):
                bonus += 0.05
        
        return bonus
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate improvement recommendations based on test results.
        
        Args:
            results: Test results
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Overall score assessment
        overall_score = results['overall_score']
        if overall_score < 0.7:
            recommendations.append(
                f"Overall quality score is {overall_score:.1%}. "
                "Consider completing embeddings and improving chunk quality."
            )
        
        # Category-specific recommendations
        for category, scores in results['category_scores'].items():
            if scores['average_score'] < 0.6:
                recommendations.append(
                    f"{category.title()} queries performing below 60%. "
                    f"Review {category} content in manuals."
                )
        
        # System coverage assessment
        stats = results['system_stats']
        if 'embedding_coverage' in stats and stats['embedding_coverage'] < 80:
            recommendations.append(
                f"Embedding coverage at {stats['embedding_coverage']}%. "
                "Complete embeddings for better response quality."
            )
        
        # Fallback mode assessment
        fallback_queries = sum(
            1 for category_results in results['query_results'].values()
            for query_result in category_results
            if query_result['fallback_mode']
        )
        
        if fallback_queries > 0:
            recommendations.append(
                f"{fallback_queries} queries using fallback mode. "
                "Enable Gemini models for enhanced responses."
            )
        
        return recommendations
    
    def generate_quality_report(self, results: Dict[str, Any]) -> str:
        """Generate a formatted quality report.
        
        Args:
            results: Test results from run_comprehensive_test
            
        Returns:
            Formatted report string
        """
        report = []
        report.append("🔍 HUSQVARNA 701 RAG SYSTEM QUALITY REPORT")
        report.append("=" * 50)
        report.append("")
        
        # System overview
        stats = results['system_stats']
        report.append("📊 SYSTEM OVERVIEW:")
        if 'chunks_with_embeddings' in stats:
            report.append(f"  • Total Chunks: {stats.get('total_chunks', 'N/A')}")
            report.append(f"  • Embedding Coverage: {stats.get('embedding_coverage', 'N/A')}%")
            report.append(f"  • Unique Sources: {stats.get('unique_sources', 'N/A')}")
        report.append(f"  • Overall Quality Score: {results['overall_score']:.1%}")
        report.append("")
        
        # Category scores
        report.append("📈 CATEGORY PERFORMANCE:")
        for category, scores in results['category_scores'].items():
            score_indicator = "🟢" if scores['average_score'] >= 0.8 else "🟡" if scores['average_score'] >= 0.6 else "🔴"
            report.append(f"  {score_indicator} {category.title()}: {scores['average_score']:.1%} ({scores['query_count']} queries)")
        report.append("")
        
        # Top performing queries
        all_results = []
        for category_results in results['query_results'].values():
            all_results.extend(category_results)
        
        top_queries = sorted(all_results, key=lambda x: x['quality_score'], reverse=True)[:3]
        report.append("🏆 TOP PERFORMING QUERIES:")
        for i, query_result in enumerate(top_queries, 1):
            report.append(f"  {i}. \"{query_result['query']}\" - {query_result['quality_score']:.1%}")
        report.append("")
        
        # Recommendations
        if results['recommendations']:
            report.append("💡 RECOMMENDATIONS:")
            for i, rec in enumerate(results['recommendations'], 1):
                report.append(f"  {i}. {rec}")
        report.append("")
        
        return "\n".join(report)


def main():
    """Main function for running advanced tests."""
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    if not project_id:
        print("Error: Set GOOGLE_CLOUD_PROJECT environment variable")
        return
    
    print("🚀 Starting Advanced RAG System Quality Assessment...")
    print(f"Project: {project_id}")
    print("=" * 60)
    
    tester = AdvancedQueryTester(project_id)
    results = tester.run_comprehensive_test()
    
    # Generate and display report
    report = tester.generate_quality_report(results)
    print(report)
    
    # Save detailed results
    import json
    with open('rag_quality_assessment.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print("📄 Detailed results saved to: rag_quality_assessment.json")


if __name__ == "__main__":
    main() 