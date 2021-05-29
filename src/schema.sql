CREATE TABLE customer
(
    id            TEXT    PRIMARY KEY NOT NULL,
    first_name    TEXT                NOT NULL,
    last_name     TEXT                NOT NULL,
    email         TEXT                NOT NULL,
    password_hash TEXT                NOT NULL,
    phone_number  TEXT                NOT NULL,
    created_at    DATETIME            NOT NULL,
    group_name    TEXT                NOT NULL
);
CREATE INDEX customer_email ON customer (email);

CREATE TABLE address
(
    customer_id TEXT    PRIMARY KEY NOT NULL,
    country     TEXT                NOT NULL,
    city        TEXT                NOT NULL,
    street      TEXT                NOT NULL,
    apartment   TEXT                NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customer (id)
);

CREATE TABLE visit
(
    id          INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    customer_id TEXT             NOT NULL,
    visit_at    DATETIME         NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customer (id)
);

CREATE TABLE customer_order
(
    id           TEXT PRIMARY KEY NOT NULL,
    created_at   DATETIME         NOT NULL,
    payment_type TEXT             NOT NULL,
    visit_id     INTEGER          NOT NULL,
    FOREIGN KEY (visit_id) REFERENCES visit (id)
);

CREATE TABLE product
(
    id       INTEGER PRIMARY KEY NOT NULL,
    name     TEXT                NOT NULL,
    price    REAL                NOT NULL,
    category TEXT                NOT NULL
);

CREATE TABLE ordered_product
(
    id         INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    product_id INTEGER             NOT NULL,
    order_id   TEXT                NOT NULL,
    FOREIGN KEY (product_id) REFERENCES product (id),
    FOREIGN KEY (order_id) REFERENCES customer_order (id)
);