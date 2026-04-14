DROP TABLE IF EXISTS Observation;
DROP TABLE IF EXISTS Species;
DROP TABLE IF EXISTS Recording;
DROP TABLE IF EXISTS Recording_staging;
DROP TABLE IF EXISTS Recording_duplicates;
DROP TABLE IF EXISTS Recording_validation;
DROP TABLE IF EXISTS Microphone;

CREATE TABLE IF NOT EXISTS Microphone(
    id VARCHAR(10) NOT NULL,
    longitude DECIMAL(9,6),
    latitude DECIMAL(8,6),
    description VARCHAR(500),

    PRIMARY KEY (id)
);


CREATE TABLE IF NOT EXISTS Recording_staging(
    id VARCHAR(64),
    file_name VARCHAR(255),
    microphone_id VARCHAR(10),
    rec_date DATE,
    start_time TIME,
    stop_time TIME,
    duration INT,
    file_path VARCHAR(255),
    file_size INT,
    samplerate INT,
    channels INT,
    bitdepth INT,
    file_hash CHAR(64),
    batch_id INT NOT NULL,
    ingestion_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);


CREATE TABLE IF NOT EXISTS Recording_rejected(
    id VARCHAR(64),
    file_name VARCHAR(255),
    microphone_id VARCHAR(10),
    rec_date DATE,
    start_time TIME,
    stop_time TIME,
    duration INT,
    file_path VARCHAR(255),
    file_size INT,
    samplerate INT,
    channels INT,
    bitdepth INT,
    file_hash CHAR(64),
    batch_id INT,
    is_duplicate BOOLEAN DEFAULT False,
    duplicate_type ENUM('batch', 'historical') DEFAULT NULL,
    is_null BOOLEAN DEFAULT False,
    rejected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS Recording_cleaned(
    id VARCHAR(64) NOT NULL UNIQUE,
    file_name VARCHAR(255),
    microphone_id VARCHAR(10) NOT NULL,
    rec_date DATE NOT NULL,
    start_time TIME NOT NULL,
    stop_time TIME NOT NULL,
    duration INT NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    file_size INT NOT NULL,
    samplerate INT NOT NULL,
    channels INT NOT NULL,
    bitdepth INT NOT NULL,
    file_hash CHAR(64) UNIQUE NOT NULL

    PRIMARY KEY (id),
    FOREIGN KEY (microphone_id) REFERENCES Microphone(id) -- make this a check. Recordings must be matched to a mic
);


CREATE TABLE IF NOT EXISTS Recording(
    id VARCHAR(64) NOT NULL UNIQUE,
    file_name VARCHAR(255),
    microphone_id VARCHAR(10) NOT NULL,
    rec_date DATE NOT NULL,
    start_time TIME NOT NULL,
    stop_time TIME NOT NULL,
    duration INT NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    file_size INT NOT NULL,
    samplerate INT NOT NULL,
    channels INT NOT NULL,
    bitdepth INT NOT NULL,
    file_hash CHAR(64) UNIQUE NOT NULL,

    PRIMARY KEY (id),
    FOREIGN KEY (microphone_id) REFERENCES Microphone(id)
);

CREATE TABLE IF NOT EXISTS Species(
    id INT NOT NULL,
    scientific_name VARCHAR(300) NOT NULL,
    common_name_eng VARCHAR(300) NOT NULL,
    common_name_nl VARCHAR(300),

    PRIMARY KEY (id, scientific_name)
);

CREATE TABLE IF NOT EXISTS Observation(
    id INT NOT NULL,
    rec_id VARCHAR(64) NOT NULL,
    species_id INT NOT NULL,
    start_second INT NOT NULL,
    stop_second INT NOT NULL,
    confidence_score FLOAT NOT NULL,

    PRIMARY KEY (id),
    FOREIGN KEY (rec_id) REFERENCES Recording(id),
    FOREIGN KEY (species_id) REFERENCES Species(id)
);