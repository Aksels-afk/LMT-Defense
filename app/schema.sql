CREATE TABLE bases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL /* [1] */
);

CREATE TABLE interceptor_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    speed_ms REAL NOT NULL,
    range_m REAL NOT NULL,
    max_altitude_m REAL NOT NULL,
    price_model TEXT NOT NULL,
    price_value_eur DECIMAL(10,2) NOT NULL
);

CREATE TABLE base_interceptors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    base_id INT NOT NULL,
    interceptor_id INT NOT NULL,
    UNIQUE (base_id, interceptor_id),
    FOREIGN KEY (base_id) REFERENCES bases(id),
    FOREIGN KEY (interceptor_id) REFERENCES interceptor_types(id)
);
-- Insert bases
INSERT INTO bases (name, latitude, longitude) VALUES
    ('Riga', 56.97475845607155, 24.1670070219384),
    ('Liepaja', 56.516083346891044, 21.0182217849017),
    ('Daugavpils', 55.87409588616014, 26.51864225209475);

-- Insert Interceptor Types
INSERT INTO interceptor_types (name, speed_ms, range_m, max_altitude_m, price_model, price_value_eur) VALUES
    ('Interceptor drone', 80.00, 30000.00, 2000.00, 'flat', 10000.00),
    ('Fighter jet', 700.00, 3500.00, 15000.00, 'per_minute', 1000.00),
    ('Rocket', 1500.00, 100000.00, 30000.00, 'flat', 300000.00),
    ('50Cal', 900.00, 2000.00, 2000.00, 'per_shot', 1.00);

INSERT INTO base_interceptors (base_id, interceptor_id) VALUES
    -- Riga has all types (id 1)
    (1,1),
    (1,2),
    (1,3),
    (1,4);
INSERT INTO base_interceptors (base_id, interceptor_id) VALUES
    -- Liepaja has only drone and 50Cal (id 2)
    (2,1),
    (2,4);
INSERT INTO base_interceptors (base_id, interceptor_id) VALUES
    -- Daugavpils has drone, 50cal, rocket.
    (3,1),
    (3,3),
    (3,4);