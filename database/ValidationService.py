import pandas as pd
import logging
from sqlalchemy import select
from database.tables import Recording_cleaned, TransformationProcessedRecordings

class ValidationService:
    def __init__(self, engine):
        self.engine = engine
