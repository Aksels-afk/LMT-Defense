CREATE TABLE bases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL
);

CREATE TABLE interceptor_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    speed_ms REAL NOT NULL,
    range_m REAL NOT NULL,
    max_altitude_m REAL NOT NULL,
    price_model TEXT NOT NULL,
    price_value_eur REAL NOT NULL
);

CREATE TABLE base_interceptors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    base_id INTEGER NOT NULL,
    interceptor_id INTEGER NOT NULL,
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
    ('Interceptor drone', 80.00, 3000.00, 2000.00, 'flat', 10000.00),
    ('Fighter jet', 700.00, 3500.00, 15000.00, 'per_minute', 1000.00),
    ('Rocket', 1500.00, 100000.00, 30000.00, 'flat', 300000.00),
    ('50Cal', 900.00, 2000.00, 2000.00, 'per_shot', 1.00);

-- Base-interceptor availability
INSERT INTO base_interceptors (base_id, interceptor_id) VALUES
    (1, 1), -- Riga -> Interceptor drone
    (1, 2), -- Riga -> Fighter jet
    (1, 3), -- Riga -> Rocket
    (1, 4), -- Riga -> 50Cal
    (2, 1), -- Liepaja -> Interceptor drone
    (2, 4), -- Liepaja -> 50Cal
    (3, 1), -- Daugavpils -> Interceptor drone
    (3, 3), -- Daugavpils -> Rocket
    (3, 4); -- Daugavpils -> 50Cal