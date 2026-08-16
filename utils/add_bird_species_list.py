import sys
from pathlib import Path
import os
import dotenv
import pandas as pd
from Config import DatabaseConfig

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.MaintenanceService import DatabaseMaintenance
from database.Engine import Engine




if __name__ == '__main__':

    # Open and load the config
    try:
        dotenv.load_dotenv('/etc/bird_audio_pipeline.conf')
    except FileNotFoundError:
        print("ERROR: Can't find config file")
        sys.exit(0)

    database_config = DatabaseConfig(
        os.getenv('DATABASE_USER'),
        os.getenv('DATABASE_PASSWORD'),
        os.getenv('DATABASE_NAME'),
        os.getenv('DATABASE_HOST'),
        os.getenv('DATABASE_PORT')
    )



    species_list = pd.read_csv('./files/birdnet_taxonomy_0.3-Jul2026.csv', header=0)

    shortend_list = species_list[['birdnet_id', 'scientific_name', 'scientific_name_aliases', 'common_name', 'common_name_alt',
                                  'taxon_group', 'record_type', 'scientific_name_aliases',
                                  'common_name_aliases', 'inat_id', 'ebird_code', 'gbif_id', 'ncbi_id',
                                  'avibase_id', 'birdlife_id', 'ml_taxon_code', 'xc_name',
                                  'observationorg_id', 'wikidata_qid', 'observations_count',
                                  'description_source', 'metadata_quality_score',
                                  'metadata_quality_flags', 'image_url', 'image_author', 'image_license',
                                  'image_source', 'common_name_en', 'common_name_nl']]

    aves_filtered = shortend_list[shortend_list['taxon_group'] == 'Aves'].fillna('')

    print(f'Got {len(aves_filtered)} species. Writing to database...')


    db_engine = Engine(database_config)
    db_maintenance = DatabaseMaintenance(db_engine.engine)
    db_maintenance.insert_bird_species(aves_filtered)
