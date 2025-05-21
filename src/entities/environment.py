# 생물이 모든 물질을 소화할 수 있게 되면 문제 발생 -> 물질 소화를 가중치로 두고, 최대 소화율만큼 분배.
class OrganicMatterSource:
    def __init__(self, sources: list[tuple[int, int]]):
        """
        sources: 각 유기물 생성 속도와 최대량 (generation_rate, max_amount)
        """
        self.sources = sources
        self.current_amounts = [max_amount for _, max_amount in sources]

    def regenerate(self):
        """
        유기물들이 자연적으로 생성.
        """
        for i, (gen_rate, max_amount) in enumerate(self.sources):
            if self.current_amounts[i] < max_amount:
                self.current_amounts[i] = min(self.current_amounts[i] + gen_rate, max_amount)