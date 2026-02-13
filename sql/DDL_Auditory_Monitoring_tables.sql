DROP TABLE IF EXISTS Microphone;
CREATE TABLE IF NOT EXISTS Microphone(
    id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    longitude DECIMAL(9,6),
    latitude DECIMAL(8,6),
    location_description VARCHAR(500),

    PRIMARY KEY (id)
);

DROP TABLE IF EXISTS Recording;
CREATE TABLE IF NOT EXISTS Recording(
    id INT NOT NULL,
    file_name VARCHAR(255),
    microphone_id INT NOT NULL,
    rec_date DATE NOT NULL,
    start_time TIME NOT NULL,
    stop_time TIME NOT NULL,
    duration INT NOT NULL,
    filesize INT NOT NULL,
    samplerate INT NOT NULL,
    channels INT NOT NULL,
    bitdepth INT NOT NULL,


    PRIMARY KEY (id),
    FOREIGN KEY (microphone_id) REFERENCES Microphone(id)
);

DROP TABLE IF EXISTS Species;
CREATE TABLE IF NOT EXISTS Species(
    id INT NOT NULL,
    scientific_name VARCHAR(300) NOT NULL,
    common_name_eng VARCHAR(300) NOT NULL,
    common_name_nl VARCHAR(300),

    PRIMARY KEY (id, scientific_name)
);

DROP TABLE IF EXISTS Observation;
CREATE TABLE IF NOT EXISTS Observation(
    id INT NOT NULL,
    rec_id INT NOT NULL,
    species_id INT NOT NULL,
    start_second INT NOT NULL,
    stop_second INT NOT NULL,
    confidence_score FLOAT NOT NULL,

    PRIMARY KEY (id),
    FOREIGN KEY (rec_id) REFERENCES Recording(id),
    FOREIGN KEY (species_id) REFERENCES Species(id)
);