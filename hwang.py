# 개선된 시뮬레이션 코드 (PDF 요구사항 완전 반영 + GUI 최적화 및 다중 행위자 처리)
from typing import List, Dict, Optional
import random
import math
import time
import gradio as gr
import matplotlib.pyplot as plt
import io
import base64


class Actor:
    def __init__(self, id: str, properties: Dict[str, float]):
        self.id = id
        self.properties = properties
        self.actions = []
        self.space = None
        self.work = None

    def perform_action(self, action_type: str, target: Optional["Actor"] = None):
        self.actions.append(action_type)
        if target:
            self._affect_target(target)

    def _affect_target(self, target: "Actor"):
        if "negotiate" in self.actions:
            target.properties["stress"] = target.properties.get("stress", 0) + 5


class Environment:
    def __init__(self, id: str, properties: Dict[str, float]):
        self.id = id
        self.properties = properties
        self.manifestations = []

    def manifest(self, manifestation_type: str, target: Optional["Environment"] = None):
        self.manifestations.append(manifestation_type)
        if manifestation_type == "competition_rise":
            self.properties["competition"] += 0.1
        if target:
            self._affect_environment(target)

    def _affect_environment(self, target: "Environment"):
        if "competition_rise" in self.manifestations:
            target.properties["demand"] *= 0.95

    def affect_actor(self, actor: Actor):
        comp = self.properties.get("competition", 0)
        if comp > 0.7:
            actor.properties["stress"] = actor.properties.get("stress", 0) + comp * 10


class Worker(Actor):
    def __init__(self, id: str, age: int, distance: float, previous_wage: float):
        super().__init__(
            id,
            {
                "age": age,
                "distance": distance,
                "previous_wage": previous_wage,
                "employed": False,
                "stress": 0,
                "efficiency": 1.0,
            },
        )
        self.negotiation_attempts = 0
        self.max_attempts = 5
        self.deduction_rate = 0.05

    def negotiate_wage(self, population: int) -> float:
        if self.negotiation_attempts >= self.max_attempts:
            return 0

        base = self.properties["previous_wage"]
        distance_factor = self.properties["distance"] * 1000
        age_factor = self._calculate_age_factor()
        population_factor = math.log(population + 1) * 1000

        wage = base + distance_factor + age_factor + population_factor
        wage *= 1 - self.deduction_rate * self.negotiation_attempts
        self.negotiation_attempts += 1
        return wage

    def _calculate_age_factor(self) -> float:
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
        base_production = self.properties["property_size"] * 1_000_000
        labor_cost_ratio = 0.4
        return max(1, int(base_production * labor_cost_ratio / wage))

    def calculate_profit(self, wage: float, num_workers: int) -> float:
        comp = self.space.environments[0].properties["competition"]
        prod_per_worker = 3_500_000 * (1 + comp)
        production = prod_per_worker * num_workers
        cost = wage * num_workers + production * 0.1
        return production - cost


class World:
    def __init__(self):
        self.actors: List[Actor] = []
        self.environments: List[Environment] = []
        self.population = 0

    def add_actor(self, actor: Actor):
        self.actors.append(actor)
        actor.space = self

    def add_environment(self, environment: Environment):
        self.environments.append(environment)

    def update(self):
        for env in self.environments:
            for actor in self.actors:
                env.affect_actor(actor)

        for actor in self.actors:
            if "stress" in actor.properties and "efficiency" in actor.properties:
                stress = actor.properties["stress"]
                actor.properties["efficiency"] = max(0.5, 1.0 - 0.01 * stress)


def run_simulation(
    market_competition: float,
    initial_wage: float,
    sim_count: int,
    initial_population: int,
    worker_count: int,
) -> str:
    results = ["시뮬레이션 환경 초기화 중...\n"]

    try:
        world = World()
        world.population = initial_population

        env1 = Environment(
            "market", {"demand": 1000, "supply": 800, "competition": market_competition}
        )
        env2 = Environment(
            "secondary", {"demand": 900, "supply": 850, "competition": 0.3}
        )
        world.add_environment(env1)
        world.add_environment(env2)

        for i in range(sim_count):
            results.append(f"\n시뮬레이션 {i+1} 시작:\n")

            workers = [
                Worker(
                    f"worker{j+1}",
                    age=20 + j,
                    distance=1.0 + j,
                    previous_wage=initial_wage,
                )
                for j in range(worker_count)
            ]
            employer = Employer("employer1", property_size=1000)
            world.add_actor(employer)
            for worker in workers:
                world.add_actor(worker)

            env1.manifest("competition_rise", target=env2)

            for worker in workers:
                for attempt in range(worker.max_attempts):
                    wage = worker.negotiate_wage(world.population)
                    optimal_workers = employer.calculate_optimal_employment(wage)
                    profit = employer.calculate_profit(wage, optimal_workers)

                    results.append(f"{worker.id} 협상 시도 {attempt + 1}:\n")
                    results.append(f"- 제시 임금: {wage:,.0f}원\n")
                    results.append(f"- 최적 고용자 수: {optimal_workers}명\n")
                    results.append(f"- 예상 이익: {profit:,.0f}원\n")

                    if profit > 0:
                        employer.perform_action("negotiate", worker)
                        worker.properties["employed"] = True
                        worker.work = "생산"
                        worker.space = employer.space
                        results.append("→ 협상 성공!\n")
                        break
                    else:
                        results.append("→ 협상 실패, 재시도...\n")

            world.update()
            time.sleep(0.2)

        results.append("\n모든 시뮬레이션이 완료되었습니다!\n")
        results.append("-" * 40 + "\n")

    except Exception as e:
        results.append(f"시뮬레이션 중 오류 발생: {str(e)}\n")

    return "".join(results)


def plot_simulation_results(
    profits_per_simulation: List[float], average_wages: List[float]
) -> str:
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 8))

    ax1.plot(
        range(1, len(profits_per_simulation) + 1), profits_per_simulation, marker="o"
    )
    ax1.set_title("Total Profit per Simulation")
    ax1.set_xlabel("Simulation Number")
    ax1.set_ylabel("Total Profit (₩)")
    ax1.grid(True)

    ax2.plot(
        range(1, len(average_wages) + 1), average_wages, marker="x", color="orange"
    )
    ax2.set_title("Average Wage per Simulation")
    ax2.set_xlabel("Simulation Number")
    ax2.set_ylabel("Average Wage (₩)")
    ax2.grid(True)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()
    plt.close(fig)
    return f"<img src='data:image/png;base64,{image_base64}'/>"


def run_simulation_with_plot(
    market_competition: float,
    initial_wage: float,
    sim_count: int,
    initial_population: int,
    worker_count: int,
) -> tuple[str, str]:
    results = ["Initializing simulation environment...\n"]
    total_profits = []
    average_wages = []

    try:
        world = World()
        world.population = initial_population

        env1 = Environment(
            "market", {"demand": 1000, "supply": 800, "competition": market_competition}
        )
        env2 = Environment(
            "secondary", {"demand": 900, "supply": 850, "competition": 0.3}
        )
        world.add_environment(env1)
        world.add_environment(env2)

        for i in range(sim_count):
            results.append(f"\nSimulation {i+1} Start:\n")
            sim_profit = 0
            wage_sum = 0
            wage_count = 0

            workers = [
                Worker(
                    f"worker{j+1}",
                    age=20 + j,
                    distance=1.0 + j,
                    previous_wage=initial_wage,
                )
                for j in range(worker_count)
            ]
            employer = Employer("employer1", property_size=1000)
            world.add_actor(employer)
            for worker in workers:
                world.add_actor(worker)

            env1.manifest("competition_rise", target=env2)

            for worker in workers:
                for attempt in range(worker.max_attempts):
                    wage = worker.negotiate_wage(world.population)
                    optimal_workers = employer.calculate_optimal_employment(wage)
                    profit = employer.calculate_profit(wage, optimal_workers)

                    results.append(f"{worker.id} Negotiation Attempt {attempt + 1}:\n")
                    results.append(f"- Proposed Wage: ₩{wage:,.0f}\n")
                    results.append(f"- Optimal Number of Workers: {optimal_workers}\n")
                    results.append(f"- Expected Profit: ₩{profit:,.0f}\n")

                    if profit > 0:
                        sim_profit += profit
                        wage_sum += wage
                        wage_count += 1
                        employer.perform_action("negotiate", worker)
                        worker.properties["employed"] = True
                        worker.work = "production"
                        worker.space = employer.space
                        results.append("→ Negotiation Successful!\n")
                        break
                    else:
                        results.append("→ Negotiation Failed, Retrying...\n")

            world.update()
            time.sleep(0.2)
            total_profits.append(sim_profit)
            avg_wage = wage_sum / wage_count if wage_count > 0 else 0
            average_wages.append(avg_wage)

        results.append("\nAll simulations completed successfully.\n")
        results.append("-" * 40 + "\n")

    except Exception as e:
        results.append(f"Simulation error occurred: {str(e)}\n")

    text_output = "".join(results)
    img_output = plot_simulation_results(total_profits, average_wages)
    return text_output, img_output


iface = gr.Interface(
    fn=run_simulation_with_plot,
    inputs=[
        gr.Slider(
            minimum=0, maximum=1, step=0.1, label="Market Competition", value=0.5
        ),
        gr.Number(label="Initial Wage", value=3000000),
        gr.Number(label="Number of Simulations", value=5, precision=0),
        gr.Number(label="Initial Population", value=1000, precision=0),
        gr.Number(label="Number of Workers", value=3, precision=0),
    ],
    outputs=[
        gr.Textbox(label="Simulation Results", lines=15),
        gr.HTML(label="Simulation Graphs"),
    ],
    title="Labor Market Simulation (Extended + Visualization)",
    description="Fully implemented PDF logic with multiple agents and graphical summary.",
    allow_flagging="never",
)

if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0", server_port=7860, share=True)
