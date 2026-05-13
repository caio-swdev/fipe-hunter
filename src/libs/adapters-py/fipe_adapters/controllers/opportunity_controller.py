"""
OpportunityController - FastAPI Controller for Opportunity Operations

Handles opportunity queries and statistics.
"""
from typing import Dict, Any, List
from fipe_business.application.ports.opportunity_repository import IOpportunityRepository


class OpportunityController:
    """Controller for opportunity operations."""

    def __init__(self, repository: IOpportunityRepository):
        """
        Initialize controller with repository dependency.

        Args:
            repository: SQLAlchemy opportunity repository instance
        """
        self.repository = repository

    def list_opportunities(self, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """
        List all opportunities sorted by score (highest first).

        Args:
            limit: Maximum number of opportunities to return
            offset: Number of opportunities to skip

        Returns:
            Response dictionary with opportunities array
        """
        try:

            opportunities = self.repository.find_active(min_score=0, limit=1000)


            sorted_opps = sorted(
                opportunities,
                key=lambda o: o.score.value if hasattr(o, 'score') else o.score_value if hasattr(o, 'score_value') else 0,
                reverse=True
            )


            paginated = sorted_opps[offset:offset + limit]


            data = []
            for opp in paginated:
                data.append({
                    "id": opp.listing_id,
                    "listing_id": opp.listing_id,
                    "brand": opp.brand,
                    "model": opp.model,
                    "year": opp.year,
                    "listing_price": float(opp.listing_price.amount) if hasattr(opp.listing_price, 'amount') else float(opp.listing_price),
                    "fipe_price": float(opp.fipe_price.amount) if hasattr(opp.fipe_price, 'amount') else float(opp.fipe_price),
                    "discount_percent": float(opp.discount.percentage) if hasattr(opp.discount, 'percentage') else float(opp.discount_percentage),
                    "discount_amount": float(opp.discount.amount.amount) if hasattr(opp.discount, 'amount') else float(opp.discount_amount),
                    "score": opp.score.value if hasattr(opp, 'score') else opp.score_value if hasattr(opp, 'score_value') else 0,
                    "marketplace": opp.marketplace,
                    "listing_url": opp.listing_url,
                    "condition": opp.condition,
                    "mileage": opp.mileage,
                    "status": opp.status,
                    "image_url": getattr(opp, 'image_url', None),
                })

            return {
                "status": "success",
                "data": data,
                "total": len(sorted_opps),
                "limit": limit,
                "offset": offset
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to list opportunities: {str(e)}",
                "data": []
            }

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for all opportunities.

        Returns:
            Response dictionary with summary stats
        """
        try:
            total = self.repository.count_by_status("active")
            opportunities = self.repository.find_active(min_score=0, limit=1000)

            if not opportunities:
                return {
                    "status": "success",
                    "data": {
                        "total_opportunities": 0,
                        "avg_discount": 0,
                        "best_score": 0,
                        "avg_savings": 0
                    }
                }

            discounts = []
            savings = []
            scores = []

            for opp in opportunities:
                discount_pct = float(opp.discount.percentage) if hasattr(opp.discount, 'percentage') else float(opp.discount_percentage)
                discount_amt = float(opp.discount.amount.amount) if hasattr(opp.discount, 'amount') else float(opp.discount_amount)
                score = opp.score.value if hasattr(opp, 'score') else opp.score_value if hasattr(opp, 'score_value') else 0

                discounts.append(discount_pct)
                savings.append(discount_amt)
                scores.append(score)

            avg_discount = sum(discounts) / total if total > 0 else 0
            avg_savings = sum(savings) / total if total > 0 else 0
            best_score = max(scores) if scores else 0

            return {
                "status": "success",
                "data": {
                    "total_opportunities": total,
                    "avg_discount": round(avg_discount, 1),
                    "best_score": best_score,
                    "avg_savings": round(avg_savings, 2)
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get summary: {str(e)}",
                "data": {
                    "total_opportunities": 0,
                    "avg_discount": 0,
                    "best_score": 0,
                    "avg_savings": 0
                }
            }
