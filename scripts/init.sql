-- Create database and user
CREATE DATABASE IF NOT EXISTS taskdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'root'@'localhost' IDENTIFIED BY '123456';
GRANT ALL PRIVILEGES ON taskdb.* TO 'root'@'localhost';
FLUSH PRIVILEGES;