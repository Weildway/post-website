CREATE TABLE users (
  id            serial PRIMARY KEY NOT NULL,
  username      text UNIQUE NOT NULL,
  password      text NOT NULL,
  register_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  is_admin      boolean NOT NULL
);

CREATE TABLE packages (
  track           uuid PRIMARY KEY NOT NULL,
  pkg_name        text NOT NULL,

  sender_id       serial NOT NULL,
  receiver_id     serial NOT NULL,

  sender_index    int NOT NULL,
  receiver_index  int NOT NULL,

  sender_addr     text NOT NULL,
  receiver_addr   text NOT NULL,

  pkg_status      text NOT NULL,
  send_date       timestamp DEFAULT CURRENT_TIMESTAMP,
  update_time     timestamp DEFAULT CURRENT_TIMESTAMP,
  delivered       boolean DEFAULT false,

  CONSTRAINT fk_sender FOREIGN KEY(sender_id) REFERENCES users(id)
);

CREATE TABLE departament (
  id        serial PRIMARY KEY NOT NULL,
  dep_name  text NOT NULL,
  dep_index int NOT NULL,
  city      text NOT NULL,
  addr      text NOT NULL
);

CREATE TABLE postmans (
  id            serial PRIMARY KEY NOT NULL,
  first_name    text NOT NULL,
  last_name     text NOT NULL,
  department_id serial NOT NULL,
  CONSTRAINT fk_dep FOREIGN KEY(department_id) REFERENCES departament(id)
);

CREATE TABLE storage (
  id          serial PRIMARY KEY NOT NULL,
  pkg_track   uuid,
  postman_id  int,
  dep_id      int,
  prev_dep_id int,
  next_dep_id int,
  CONSTRAINT fk_package FOREIGN KEY(pkg_track) REFERENCES packages(track),
  CONSTRAINT fk_postman FOREIGN KEY(postman_id) REFERENCES postmans(id),
  CONSTRAINT fk_departament FOREIGN KEY(dep_id) REFERENCES departament(id)
);