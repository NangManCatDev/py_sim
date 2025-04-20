from typing import List, Dict, Optional
import random
import math
import time
import gradio as gr
import matplotlib.pyplot as plt
import io
import base64


class Actor:
    """Base class for all actors (agents) in the simulation."""

    def __init__(self, id: str, properties: Dict[str, float]):
        self.id = id
        self.properties = properties
        self.actions: List[str] = []  # record of actions this actor has taken
        self.space: Optional["World"] = (
            None  # reference to the world (environment space)
        )
        self.work: Optional[str] = None  # current work/role assignment (if any)

    def perform_action(self, action_type: str, target: Optional["Actor"] = None):
        """Perform an action and optionally affect a target actor."""
        # Record the action performed by this actor.
        self.actions.append(action_type)
        if target:
            # If the action has a target actor, apply its effects on the target.
            self._affect_target(target)

    def _affect_target(self, target: "Actor"):
        # Relationship (1): Actor action affecting other actors' properties.
        # For example, if this actor negotiates, increase the target actor's stress.
        if "negotiate" in self.actions:
            target.properties["stress"] = target.properties.get("stress", 0) + 5


class Environment:
    """Represents an environment with certain properties and possible events (manifestations)."""

    def __init__(self, id: str, properties: Dict[str, float]):
        self.id = id
        self.properties = (
            properties  # e.g., {"demand": ..., "supply": ..., "competition": ...}
        )
        self.manifestations: List[str] = (
            []
        )  # record of events that have occurred in this environment

    def manifest(self, manifestation_type: str, target: Optional["Environment"] = None):
        """Trigger an environmental event (manifestation), optionally affecting another environment."""
        self.manifestations.append(manifestation_type)
        # Relationship (5): Environmental attributes causing its own manifestation.
        # For example, a "competition_rise" event increases this environment's competition level.
        if manifestation_type == "competition_rise":
            self.properties["competition"] += 0.1
        if target:
            # If a target environment is specified, this event also impacts the target environment.
            self._affect_environment(target)

    def _affect_environment(self, target: "Environment"):
        # Relationship (4): One environment's manifestation affecting another environment.
        # For example, increased competition here causes a 5% reduction in the target environment's demand.
        if "competition_rise" in self.manifestations:
            target.properties["demand"] *= 0.95

    def affect_actor(self, actor: Actor):
        """Apply environmental effects on an actor (e.g., high competition increases stress)."""
        # Relationship (3): Environmental properties affecting actor attributes.
        comp = self.properties.get("competition", 0)
        if comp > 0.7:
            # If competition is very high, it increases the actor's stress.
            actor.properties["stress"] = actor.properties.get("stress", 0) + comp * 10
            # Relationship (7): Environmental manifestation (e.g., a high competition event) affecting actor properties (stress).


class Worker(Actor):
    """An Actor representing a worker seeking employment."""

    def __init__(self, id: str, age: int, distance: float, previous_wage: float):
        # Initialize base Actor with worker-specific properties
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
        # Track negotiation attempts and rules
        self.negotiation_attempts: int = 0
        self.max_attempts: int = 5
        self.deduction_rate: float = 0.05  # 5% wage deduction per attempt

    def negotiate_wage(self, population: int) -> float:
        """Calculate the next wage offer based on the worker's attributes and the current population context."""
        if self.negotiation_attempts >= self.max_attempts:
            return 0  # no further negotiation attempts available

        # Calculate components influencing the wage demand:
        base = self.properties["previous_wage"]  # base wage (previous salary)
        distance_factor = (
            self.properties["distance"] * 1000
        )  # higher distance -> higher wage demand (travel compensation)
        age_factor = (
            self._calculate_age_factor()
        )  # if age < 30, this will be negative (less experience -> lower wage)
        population_factor = (
            math.log(population + 1) * 1000
        )  # larger population -> higher wage demand (more competition for jobs)

        # Combine factors to determine the proposed wage
        wage = base + distance_factor + age_factor + population_factor
        # Each attempt, reduce the wage by a fixed percentage to improve chances (wage decreases by 5% per attempt made).
        wage *= 1 - self.deduction_rate * self.negotiation_attempts
        self.negotiation_attempts += 1  # increment attempt count after proposing wage
        return wage

    def _calculate_age_factor(self) -> float:
        """Internal helper to adjust wage based on age (younger workers may have lower expected wage)."""
        age = self.properties["age"]
        if age < 30:
            # For age below 30, return a negative value proportional to how far below 30 (reducing wage demand).
            return (age - 30) * 1000
        return 0


class Employer(Actor):
    """An Actor representing an employer who can hire workers and aims to maximize profit."""

    def __init__(self, id: str, property_size: float):
        # Initialize base Actor with employer-specific properties
        super().__init__(
            id, {"property_size": property_size, "production": 0, "profit": 0}
        )
        self.workers: List[Worker] = []  # list of hired workers (initially empty)

    def calculate_optimal_employment(self, wage: float) -> int:
        """Determine the optimal number of workers to employ at the given wage (for profit maximization)."""
        # Assume base production is proportional to property size (e.g., output per unit property_size)
        base_production = self.properties["property_size"] * 1_000_000
        labor_cost_ratio = 0.4  # assume 40% of production value is the ideal labor cost
        optimal = int(base_production * labor_cost_ratio / wage)
        return max(1, optimal)  # ensure at least 1 worker is considered

    def calculate_profit(self, wage: float, num_workers: int) -> float:
        """Calculate the expected profit if hiring num_workers at the given wage."""
        comp = self.space.environments[0].properties[
            "competition"
        ]  # competition level in main environment
        prod_per_worker = 3_500_000 * (
            1 + comp
        )  # base productivity per worker adjusted by competition (more competition could boost market size)
        production = prod_per_worker * num_workers
        cost = (
            wage * num_workers + production * 0.1
        )  # total wage cost + 10% of production as other costs (e.g., materials)
        profit = production - cost
        return profit


class World:
    """The simulation world containing all actors and environments, and handling their interactions per tick."""

    def __init__(self):
        self.actors: List[Actor] = []
        self.environments: List[Environment] = []
        self.population: int = (
            0  # global population context (could influence actor decisions)
        )

    def add_actor(self, actor: Actor):
        """Add an actor to the world and link the world to the actor."""
        self.actors.append(actor)
        actor.space = self

    def add_environment(self, environment: Environment):
        """Add an environment to the world."""
        self.environments.append(environment)

    def update(self):
        """Update the state of the world for one time tick (apply interactions)."""
        # First, each environment affects each actor (e.g., apply stress from high competition).
        for env in self.environments:
            for actor in self.actors:
                env.affect_actor(actor)
        # Then, update each actor's internal state based on effects (e.g., adjust efficiency based on stress).
        for actor in self.actors:
            if "stress" in actor.properties and "efficiency" in actor.properties:
                stress = actor.properties["stress"]
                # Efficiency decreases with stress (1% efficiency loss per stress point), bottoming out at 50% efficiency.
                actor.properties["efficiency"] = max(0.5, 1.0 - 0.01 * stress)
        # Finally, actors' behaviors influence the environment (e.g., production from hired workers increases supply).
        for actor in self.actors:
            if isinstance(actor, Employer):
                # Relationship (6): Actor behavior affecting the environment.
                # If the employer hired workers, increase supply in the main market environment and slightly reduce demand (market saturation).
                employed_count = sum(
                    1
                    for a in self.actors
                    if isinstance(a, Worker) and a.properties.get("employed")
                )
                if self.environments:
                    self.environments[0].properties["supply"] += (
                        employed_count * 1000
                    )  # each employed worker adds to supply
                    self.environments[0].properties[
                        "demand"
                    ] *= 0.99  # demand decreases by 1% due to increased supply (if any)


def run_simulation(
    market_competition: float,
    initial_wage: float,
    sim_count: int,
    initial_population: int,
    worker_count: int,
) -> str:
    """
    Run the simulation multiple times (ticks) without graphical output.
    Returns a detailed log of the simulation as a string.
    """
    results: List[str] = []
    results.append(
        "시뮬레이션 환경 초기화 중...\n"
    )  # (Initializing simulation environment...)
    try:
        # Initialize the world and environments
        world = World()
        world.population = initial_population  # set initial population context
        env1 = Environment(
            "market", {"demand": 1000, "supply": 800, "competition": market_competition}
        )
        env2 = Environment(
            "secondary", {"demand": 900, "supply": 850, "competition": 0.3}
        )
        world.add_environment(env1)
        world.add_environment(env2)
        # The same environments persist through all simulation iterations, allowing their state to evolve over time.
        for i in range(sim_count):
            results.append(
                f"\n시뮬레이션 {i+1} 시작:\n"
            )  # Start of simulation iteration i+1
            # Create an employer and multiple workers for this tick
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
            # Add the employer and workers to the world (actors list)
            world.add_actor(employer)
            for worker in workers:
                world.add_actor(worker)
            # Environment event: competition rises in the main market environment, affecting the secondary environment
            env1.manifest("competition_rise", target=env2)
            # Wage negotiation between the employer and each worker
            for worker in workers:
                for attempt in range(worker.max_attempts):
                    wage = worker.negotiate_wage(world.population)
                    optimal_workers = employer.calculate_optimal_employment(wage)
                    profit = employer.calculate_profit(wage, optimal_workers)
                    # Log the negotiation attempt and calculated outcomes
                    results.append(
                        f"{worker.id} 협상 시도 {attempt + 1}:\n"
                    )  # (Negotiation attempt {n})
                    results.append(f"- 제시 임금: {wage:,.0f}원\n")  # (Proposed Wage)
                    results.append(
                        f"- 최적 고용자 수: {optimal_workers}명\n"
                    )  # (Optimal number of workers)
                    results.append(
                        f"- 예상 이익: {profit:,.0f}원\n"
                    )  # (Expected profit)
                    if profit > 0:
                        # If profit is positive, the employer hires the worker (profit-driven decision to employ)
                        employer.perform_action("negotiate", worker)
                        worker.properties["employed"] = True
                        worker.work = (
                            "생산"  # assign work (production) to the hired worker
                        )
                        worker.space = employer.space
                        results.append("→ 협상 성공!\n")  # (Negotiation successful!)
                        break  # exit the attempt loop for this worker, move to next worker
                    else:
                        results.append(
                            "→ 협상 실패, 재시도...\n"
                        )  # (Negotiation failed, retrying...)
            # Update the world state at the end of this tick (actors and environments)
            world.update()
            time.sleep(0.2)  # brief pause to simulate time progression
        results.append(
            "\n모든 시뮬레이션이 완료되었습니다!\n"
        )  # (All simulations completed!)
        results.append("-" * 40 + "\n")
    except Exception as e:
        results.append(
            f"시뮬레이션 중 오류 발생: {str(e)}\n"
        )  # (Error occurred during simulation)
    return "".join(results)


def plot_simulation_results(
    profits_per_simulation: List[float], average_wages: List[float]
) -> str:
    """Generate a plot for total profit and average wage across simulations, and return it as an HTML image."""
    # Create a figure with two subplots: one for profit, one for average wage
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 8))
    # Plot total profit per simulation
    ax1.plot(
        range(1, len(profits_per_simulation) + 1), profits_per_simulation, marker="o"
    )
    ax1.set_title("Total Profit per Simulation")
    ax1.set_xlabel("Simulation Number")
    ax1.set_ylabel("Total Profit (₩)")
    ax1.grid(True)
    # Plot average wage per simulation
    ax2.plot(
        range(1, len(average_wages) + 1), average_wages, marker="x", color="orange"
    )
    ax2.set_title("Average Wage per Simulation")
    ax2.set_xlabel("Simulation Number")
    ax2.set_ylabel("Average Wage (₩)")
    ax2.grid(True)
    plt.tight_layout()
    # Save plot to a buffer and encode as base64
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()
    plt.close(fig)
    # Return an HTML <img> tag with the base64-encoded image
    return f"<img src='data:image/png;base64,{image_base64}'/>"


# 변경된 run_simulation_with_plot 함수 예시:
def run_simulation_with_plot(
    market_competition: float,
    initial_wage: float,
    sim_count: int,
    _unused_population: int,
    worker_count: int,
) -> tuple[str, str]:
    results = ["📘 Initializing simulation environment...\n"]
    total_profits = []
    average_wages = []

    # ✅ 상태 유지용 객체는 반복문 밖에서 생성하여 누적 구조 유지
    world = World()
    env1 = Environment(
        "market", {"demand": 1000, "supply": 800, "competition": market_competition}
    )
    env2 = Environment("secondary", {"demand": 900, "supply": 850, "competition": 0.3})
    world.add_environment(env1)
    world.add_environment(env2)

    # ✅ 고정 employer 객체 (tick마다 유지)
    employer = Employer("employer1", property_size=1000)
    world.add_actor(employer)

    # ✅ 누적 노동자 풀 (스트레스 등 상태 유지됨)
    import numpy as np

    workers = [
        Worker(
            f"worker{j+1}",
            age=np.random.randint(20, 60),
            distance=round(np.random.uniform(1.0, 5.0), 2),
            previous_wage=np.random.randint(
                int(initial_wage * 0.8), int(initial_wage * 1.2)
            ),
        )
        for j in range(worker_count)
    ]
    for w in workers:
        world.add_actor(w)

    for i in range(sim_count):
        results.append(f"\n🔁 Tick {i+1}\n")
        sim_profit = 0.0
        wage_sum = 0.0
        wage_count = 0

        env1.manifest("competition_rise", target=env2)  # 환경 변화 발생 (누적됨)

        for worker in workers:
            if worker.properties.get("employed"):
                continue  # 이미 고용된 경우 생략

            for attempt in range(worker.max_attempts):
                wage = worker.negotiate_wage()  # ✅ population 제거
                optimal_workers = employer.calculate_optimal_employment(wage)
                profit = employer.calculate_profit(wage, 1)  # 단일 노동자 기준
                efficiency = worker.properties.get("efficiency", 1.0)

                results.append(
                    f"{worker.id} (eff={efficiency:.2f}) Attempt {attempt+1}: wage={wage:,.0f}, profit={profit:,.0f}\n"
                )

                if profit > 0 and efficiency >= 0.6:
                    sim_profit += profit
                    wage_sum += wage
                    wage_count += 1
                    employer.perform_action("negotiate", worker)
                    worker.properties["employed"] = True
                    worker.work = "production"
                    results.append("→ ✅ Hired\n")
                    break
                else:
                    results.append("→ ❌ Rejected\n")

        world.update()
        total_profits.append(sim_profit)
        avg_wage = wage_sum / wage_count if wage_count > 0 else 0
        average_wages.append(avg_wage)
        time.sleep(0.1)

    results.append("\n✔ All ticks completed.\n")
    return "".join(results), plot_simulation_results(total_profits, average_wages)


# ✅ Worker 내부 wage 계산 함수도 population 제거 필요
Worker.negotiate_wage = lambda self: (
    (
        self.properties["previous_wage"]
        + self.properties["distance"] * 1000
        + ((self.properties["age"] - 30) * 1000 if self.properties["age"] < 30 else 0)
    )
    * (1 - self.deduction_rate * self.negotiation_attempts)
    if self.negotiation_attempts < self.max_attempts
    else 0 if not self.properties.get("employed") else 0
)

iface = gr.Interface(
    fn=run_simulation_with_plot,
    inputs=[
        gr.Slider(
            minimum=0, maximum=1, step=0.1, label="Market Competition", value=0.5
        ),
        gr.Number(label="Initial Wage", value=3000000),
        gr.Number(label="Number of Simulations", value=5, precision=0),
        gr.Number(label="(Unused) Initial Population", value=1000, precision=0),
        gr.Number(label="Number of Workers", value=10, precision=0),
    ],
    outputs=[
        gr.Textbox(label="Simulation Results", lines=20),
        gr.HTML(label="Simulation Graphs"),
    ],
    title="PDF 정확 반영 시뮬레이션 (v2, no population)",
    description="population 개념 제거 및 PDF 기준에 따른 임금 산정 구조 반영 버전.",
    allow_flagging="never",
)

iface.launch(server_name="0.0.0.0", server_port=7860, share=True)
