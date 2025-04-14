from typing import List, Dict, Optional
import random
import math
import time
import gradio as gr


class Actor:
    def __init__(self, id: str, properties: Dict[str, float]):
        self.id = id
        self.properties = properties  # 행위자의 속성들
        self.actions = []  # 행위자의 행위들
        self.space = None  # 소속된 공간
        self.work = None  # 수행하는 일

    def perform_action(self, action_type: str, target: Optional["Actor"] = None):
        """행위자의 행위를 수행하는 메서드"""
        self.actions.append(action_type)
        if target:
            self._affect_target(target)

    def _affect_target(self, target: "Actor"):
        """다른 행위자의 속성에 영향을 주는 메서드"""
        # 구현은 구체적인 요구사항에 따라 달라질 수 있음
        pass


class Environment:
    def __init__(self, id: str, properties: Dict[str, float]):
        self.id = id
        self.properties = properties  # 환경의 속성들
        self.manifestations = []  # 환경의 발현들

    def manifest(self, manifestation_type: str, target: Optional["Environment"] = None):
        """환경의 발현을 수행하는 메서드"""
        self.manifestations.append(manifestation_type)
        if target:
            self._affect_environment(target)

    def _affect_environment(self, target: "Environment"):
        """다른 환경의 속성에 영향을 주는 메서드"""
        # 구현은 구체적인 요구사항에 따라 달라질 수 있음
        pass


class Worker(Actor):
    def __init__(self, id: str, age: int, distance: float, previous_wage: float):
        super().__init__(
            id,
            {
                "age": age,
                "distance": distance,
                "previous_wage": previous_wage,
                "employed": False,
            },
        )
        self.negotiation_attempts = 0
        self.max_attempts = 5
        self.deduction_rate = 0.05

    def negotiate_wage(self, population: int) -> float:
        """임금 협상을 시도하는 메서드"""
        if self.negotiation_attempts >= self.max_attempts:
            return 0

        base_wage = self.properties["previous_wage"] * (
            1 + random.normalvariate(0, 0.1)
        )
        distance_factor = self.properties["distance"] * 1000  # km당 1000원 추가
        age_factor = self._calculate_age_factor()
        population_factor = math.log(population + 1) * 1000

        wage = base_wage + distance_factor + age_factor + population_factor
        wage *= 1 - self.deduction_rate * self.negotiation_attempts

        self.negotiation_attempts += 1
        return wage

    def _calculate_age_factor(self) -> float:
        """연령에 따른 임금 조정 계수를 계산하는 메서드"""
        age = self.properties["age"]
        if age < 30:
            return (age - 30) * 1000
        return 0


class Employer(Actor):
    def __init__(self, id: str, property_size: float):
        super().__init__(
            id, {"property_size": property_size, "production": 0, "profit": 0}
        )
        self.workers: List[Worker] = []

    def calculate_optimal_employment(self, wage: float) -> int:
        """최적의 고용자 수를 계산하는 메서드"""
        # 생산량과 고용자 수의 관계를 고려한 최적화
        # 이는 실제 구현에서 더 복잡한 계산이 필요할 수 있음
        base_production = self.properties["property_size"] * 100
        optimal_workers = int(base_production / (wage * 0.1))
        return max(1, optimal_workers)

    def calculate_profit(self, wage: float, num_workers: int) -> float:
        """이익을 계산하는 메서드"""
        production = self.properties["property_size"] * num_workers * 100
        costs = wage * num_workers
        return production - costs


class World:
    def __init__(self):
        self.actors: List[Actor] = []
        self.environments: List[Environment] = []
        self.population = 0

    def add_actor(self, actor: Actor):
        self.actors.append(actor)

    def add_environment(self, environment: Environment):
        self.environments.append(environment)

    def update(self):
        """시스템의 상태를 업데이트하는 메서드"""
        # 각 행위자와 환경의 상태를 업데이트
        for actor in self.actors:
            if isinstance(actor, Worker):
                if not actor.properties["employed"]:
                    wage = actor.negotiate_wage(self.population)
                    # 고용주와의 협상 로직 구현 필요


def run_simulation(
    market_competition: float, initial_wage: float, sim_count: int
) -> str:
    results = []
    results.append("시뮬레이션 환경 초기화 중...\n")

    try:
        for i in range(sim_count):
            world = World()
            environment = Environment(
                "market",
                {"demand": 1000, "supply": 800, "competition": market_competition},
            )
            world.add_environment(environment)

            worker = Worker("worker1", 25, 5.0, initial_wage)
            employer = Employer("employer1", 1000)

            world.add_actor(worker)
            world.add_actor(employer)

            results.append(f"\n시뮬레이션 {i+1} 시작:\n")

            wage = worker.negotiate_wage(1000)
            results.append(f"협상 임금: {wage:,.0f}원\n")

            optimal_workers = employer.calculate_optimal_employment(wage)
            results.append(f"최적 고용자 수: {optimal_workers}명\n")

            profit = employer.calculate_profit(wage, optimal_workers)
            results.append(f"예상 이익: {profit:,.0f}원\n")

            time.sleep(0.5)

        results.append("\n모든 시뮬레이션이 완료되었습니다!\n")
        results.append("-" * 40 + "\n")

    except Exception as e:
        results.append(f"시뮬레이션 중 오류 발생: {str(e)}\n")

    return "".join(results)


# Gradio 인터페이스 생성
iface = gr.Interface(
    fn=run_simulation,
    inputs=[
        gr.Slider(minimum=0, maximum=1, step=0.1, label="시장 경쟁도", value=0.5),
        gr.Number(label="초기 임금", value=3000000),
        gr.Slider(minimum=1, maximum=10, step=1, label="시뮬레이션 횟수", value=5),
    ],
    outputs=gr.Textbox(label="시뮬레이션 결과", lines=10),
    title="노동 시장 시뮬레이션",
    description="시장 경쟁도와 초기 임금을 설정하여 노동 시장 시뮬레이션을 실행합니다.",
)

if __name__ == "__main__":
    iface.launch()
