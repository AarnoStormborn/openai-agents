from agents import (
    Agent, Runner, function_tool
)

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
    

