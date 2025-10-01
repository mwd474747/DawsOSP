class Relationships:
    """Define all relationship types in the system"""
    
    # Causal relationships
    CAUSES = 'causes'
    CAUSED_BY = 'caused_by'
    CONTRIBUTES = 'contributes'
    PREVENTS = 'prevents'
    
    # Correlation relationships
    CORRELATES = 'correlates'
    INVERSE = 'inverse_correlation'
    INDEPENDENT = 'independent'
    
    # Temporal relationships
    LEADS = 'leads'
    LAGS = 'lags'
    COINCIDENT = 'coincident'
    PRECEDES = 'precedes'
    FOLLOWS = 'follows'
    
    # Market relationships
    PRICES_IN = 'prices_in'
    IGNORES = 'ignores'
    OVERREACTS = 'overreacts'
    UNDERREACTS = 'underreacts'
    
    # Structural relationships
    PART_OF = 'part_of'
    CONTAINS = 'contains'
    AFFECTS = 'affects'
    DEPENDS_ON = 'depends_on'
    COMPETES_WITH = 'competes_with'
    COMPLEMENTS = 'complements'
    
    # Influence relationships
    SUPPORTS = 'supports'
    PRESSURES = 'pressures'
    WEAKENS = 'weakens'
    STRENGTHENS = 'strengthens'
    
    # Strength modifiers
    VERY_STRONG = 1.0
    STRONG = 0.8
    MODERATE = 0.6
    WEAK = 0.4
    VERY_WEAK = 0.2
    
    @classmethod
    def get_opposite(cls, relationship: str) -> str:
        """Get the opposite relationship"""
        opposites = {
            cls.CAUSES: cls.CAUSED_BY,
            cls.CAUSED_BY: cls.CAUSES,
            cls.SUPPORTS: cls.PRESSURES,
            cls.PRESSURES: cls.SUPPORTS,
            cls.STRENGTHENS: cls.WEAKENS,
            cls.WEAKENS: cls.STRENGTHENS,
            cls.LEADS: cls.LAGS,
            cls.LAGS: cls.LEADS,
            cls.PRECEDES: cls.FOLLOWS,
            cls.FOLLOWS: cls.PRECEDES
        }
        return opposites.get(relationship, relationship)
    
    @classmethod
    def is_positive(cls, relationship: str) -> bool:
        """Check if relationship has positive influence"""
        positive = [
            cls.CAUSES, cls.CORRELATES, cls.SUPPORTS,
            cls.STRENGTHENS, cls.CONTRIBUTES, cls.COMPLEMENTS
        ]
        return relationship in positive
    
    @classmethod
    def is_negative(cls, relationship: str) -> bool:
        """Check if relationship has negative influence"""
        negative = [
            cls.PRESSURES, cls.WEAKENS, cls.PREVENTS,
            cls.INVERSE, cls.COMPETES_WITH
        ]
        return relationship in negative