import os
import nest_asyncio
nest_asyncio.apply()

MODEL = os.getenv("OPENAI_MODEL")

from agents import (
    Agent, Runner, function_tool, handoff,
    RunContextWrapper, TResponseInputItem
)
from agents.extensions import handoff_filters

from pydantic import BaseModel
from enum import Enum

###############################
## Multi Agent Collaboration ##
###############################


# Defining Custom types

class UserFitnessProfile(BaseModel):
    name: str
    age: int
    weight: int
    height: float
    food_preference: str
    fitness_goal: str
    
class DietPlan(BaseModel):
    description: str
    target_calories: int
    protien_target: int
    breakfast: str
    lunch: str
    dinner: str
    
class IntensityLevel(Enum):
    Low = "Low"
    Medium = "Medium"
    High = "High"
    
class WorkoutPlan(BaseModel):
    description: str
    intensity: IntensityLevel
    frequency: int
    full_workout_plan: str
    
class Report(BaseModel):
    user_fitness_profile: UserFitnessProfile | None
    diet_plan: DietPlan | None
    workout_plan: WorkoutPlan | None
    


# Tools

@function_tool
def view_current_report(wrapper: RunContextWrapper[Report]):
    """View the current report for the User. Provides context for
    UserFitnessProfile, DietPlan, and WorkoutPlan"""
    try:
        return f"Current Report: {wrapper.context.model_dump_json()}"
    except Exception as e:
        print(e)
        return f"Error viewing report: {e}"
    
    
@function_tool
def save_user_fitness_profile(wrapper: RunContextWrapper[Report], name:str, age:int, weight:float, height:float, food_preference:str, fitness_goal:str) -> bool:
    """Save the user's fitness profile
    
    Args:
        name (str): User's name
        age (int): User's age
        weight (float): User's weight in pounds
        height (float): User's height in inches
        food_preference (str): User's food preference (e.g., vegetarian, vegan, etc.)
        fitness_goal (str): User's fitness goal (e.g., weight loss, muscle gain, etc.)
    Returns:
        bool: True if the fitness profile was saved successfully
    Raises:
        Exception: If there was an error saving the fitness profile"""
        
    try:
        wrapper.context.user_fitness_profile = UserFitnessProfile(
            name=name,
            age=age,
            weight=weight,
            height=height,
            food_preference=food_preference,
            fitness_goal=fitness_goal
        )
        print(f"Saved user fitness profile: {wrapper.context.user_fitness_profile.model_dump_json()}")
        return True
    except Exception as e:
        print(f"Failed to save user fitness profile: {e}")
        raise
    
    
@function_tool
def save_diet_plan(wrapper: RunContextWrapper[Report], description:str, target_calories:int, protein_target:int, breakfast:str, lunch:str, dinner:str) -> bool:
    """Saves the diet plan for the user.

    Args:
        description (str): Full description of the diet plan
        target_calories (int): Total target calories per day
        protein_target (int): Total protein target per day
        breakfast (str): Breakfast meal
        lunch (str): Lunch meal
        dinner (str): Dinner meal
        
    Returns:
        bool: True if the diet plan was saved successfully
        
    Raises:
        Exception: If there was an error saving the diet plan
    """
    try:
        wrapper.context.diet_plan = DietPlan(
            description=description,
            target_calories=target_calories,
            protein_target=protein_target,
            breakfast=breakfast,
            lunch=lunch,
            dinner=dinner
        )
        print(f"Saved diet plan: {wrapper.context.diet_plan.model_dump_json()}")
        return True
    except Exception as e:
        print(f"Failed to save diet plan: {e}")
        raise
    
    
@function_tool
def save_workout_plan(wrapper: RunContextWrapper[Report], description:str, intensity:IntensityLevel, frequency:int, full_workout_plan:str) -> bool:
    """Saves the workout plan for the user.

    Args:
        description (str): Description of the workout plan
        intensity (IntensityLevel): Intensity level of the workout plan
        frequency (int): Frequency of the workout plan (days per week)
        full_workout_plan (str): Complete markdown workout plan
    
    Returns
        bool: True if the workout plan was saved successfully
    
    Raises:
        Exception: If there was an error saving the workout plan
    """
    
    try:
        wrapper.context.diet_plan = WorkoutPlan(
            description=description,
            intensity=intensity,
            frequency=frequency,
            full_workout_plan=full_workout_plan
        )
        print(f"Saved workout plan: {wrapper.context.workout_plan.model_dump_json()}")
    except Exception as e:
        print(f"Failed to save diet plan: {e}")
        raise
    
    
@function_tool
def save_complete_report(wrapper: RunContextWrapper[Report], report_name:str):
    """Saves the completed report locally including the UserFitnessProfile, WorkoutPlan and DietPlan generated.
    Use this tool to save the final report once all the details are gathered.

    Args:
        report_name (str): Report file name (ex: John_Doe_Report)
    """
    try:
        with open(f"./reports/{report_name}_report.md", "w") as f:
            f.write(wrapper.context.model_dump_json())
    except Exception as e:
        print(f"Failed to save report: {e}")
        raise
    

@function_tool
def save_markdown_report(report: str, name:str):
    """Saves the full markdown report locally for a given fitness plan.
    Use this tool to save the final report once all the details are gathered.
    You must provide the full report as a markdown string.

    Args:
        report (str): Full markdown report
        name (str): Users name
    """
    try:
        with open(f"./reports/{name}_report.md", "w") as f:
            f.write(report)
    except Exception as e:
        print(f"Failed to save report: {e}")
        raise
    
    
async def start_chat(primary_agent: Agent, chat: list[TResponseInputItem]):
   
    print("NOTE: Chat started. You can type 'EXIT' to exit the conversation.")
    print("-----------------------------------------")
    report = Report(user_fitness_profile=None, diet_plan=None, workout_plan=None)
    while True:
        
        user_input = input("You: ")
        
        if user_input == "EXIT":
            print("Fitness Assistant: Goodbye!", "\n")
            break
        
        chat.append({
            "content": user_input,
            "role" : "user",
            "type": "message"
        })
        
        result = await Runner.run(
            starting_agent=primary_agent, 
            input=chat,
            context=report
        )
        
        chat.clear()
        chat.extend(result.to_input_list())

        print(f"{result.last_agent.name}:", result.final_output, "\n", flush=True)
        
        
########### Agents #############

fitness_agent = Agent(
    name="Fitness Assistant",
    instructions="""
    You are a personal assistant that gathers information on a users fitness
    profile and their preferences. You begin by asking a list of questions to
    understand the user. Once you have the information, you save the gathered
    information using the tool and handover to the Workout Planner to build a
    workout plan. Once the workout plan is built, you handover to the Diet
    Planner to build a diet plan. Once both the workout and diet plans are built,
    you explain the plan and get the User's confirmation to save the final report
    using the tool.
    """,
    model=MODEL,
    tools=[view_current_report, save_user_fitness_profile, save_markdown_report]
)

workout_planner = Agent(
    name="Workout Planner",
    instructions="""
    You are an expert workout planner. View the current report
    to retrieve the UserFitnessProfile and ask questions to build
    a workout plan for the User. Once you have the information,
    you save the gathered information using the tool and handover
    back to the Fitness Planner.
    """,
    model=MODEL,
    handoffs=[handoff(
        agent=fitness_agent,
        input_filter=handoff_filters.remove_all_tools
    )],
    tools=[view_current_report, save_workout_plan]
)      

diet_planner = Agent(
    name="Diet Planner",
    instructions="""
    You are an expert building diet plans that tailor to a User's
    fitness goals. View the current report to retrieve the UserFitnessProfil
    and WorkoutPlan and generate a diet plan to reach the User's goals.
    Feel free to ask questions to the user to gather more information.
    Once you have the information, you save the gathered information using
    the tool and handover to the Fitness Assistant to explain and save the plan.
    """,
    model=MODEL,
    handoffs=[handoff(
        agent=fitness_agent,
        input_filter=handoff_filters.remove_all_tools
    )]
)

fitness_agent.handoffs = [handoff(workout_planner), handoff(diet_planner)]


if __name__=="__main__":
    
    import asyncio
    
    chat = []
    result = asyncio.run(start_chat(fitness_agent, chat))
    
    print(f"\nFinal Result: {result}")

