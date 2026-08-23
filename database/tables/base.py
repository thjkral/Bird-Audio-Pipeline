from sqlalchemy import MetaData
from corvium_core.database.tables import Media
from corvium_core.database.tables import Device
from corvium_core.database.tables import Season

pipeline_metadata = MetaData()

Media.to_metadata(pipeline_metadata)
Device.to_metadata(pipeline_metadata)
Season.to_metadata(pipeline_metadata)