-- MySQL dump 10.13  Distrib 8.0.44, for Win64 (x86_64)
--
-- Host: localhost    Database: employee_management
-- ------------------------------------------------------
-- Server version	8.0.44

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `admin_login`
--

DROP TABLE IF EXISTS `admin_login`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `admin_login` (
  `admin_id` int NOT NULL,
  `admin_username` varchar(255) NOT NULL,
  `admin_password` varchar(255) NOT NULL,
  PRIMARY KEY (`admin_username`),
  KEY `admin_id` (`admin_id`),
  CONSTRAINT `admin_login_ibfk_1` FOREIGN KEY (`admin_id`) REFERENCES `official` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `admin_login`
--

LOCK TABLES `admin_login` WRITE;
/*!40000 ALTER TABLE `admin_login` DISABLE KEYS */;
/*!40000 ALTER TABLE `admin_login` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `attendance`
--

DROP TABLE IF EXISTS `attendance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `attendance` (
  `emp_id` int NOT NULL,
  `entry_time` time DEFAULT NULL,
  `exit_time` time DEFAULT NULL,
  KEY `emp_id` (`emp_id`),
  CONSTRAINT `attendance_ibfk_1` FOREIGN KEY (`emp_id`) REFERENCES `official` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `attendance`
--

LOCK TABLES `attendance` WRITE;
/*!40000 ALTER TABLE `attendance` DISABLE KEYS */;
INSERT INTO `attendance` VALUES (101,'16:30:00','17:30:00');
/*!40000 ALTER TABLE `attendance` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `emp_login`
--

DROP TABLE IF EXISTS `emp_login`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `emp_login` (
  `emp_id` int NOT NULL,
  `emp_username` varchar(255) NOT NULL,
  `emp_password` varchar(255) NOT NULL,
  PRIMARY KEY (`emp_username`),
  KEY `emp_id` (`emp_id`),
  CONSTRAINT `emp_login_ibfk_1` FOREIGN KEY (`emp_id`) REFERENCES `official` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `emp_login`
--

LOCK TABLES `emp_login` WRITE;
/*!40000 ALTER TABLE `emp_login` DISABLE KEYS */;
INSERT INTO `emp_login` VALUES (101,'ASD','ds_password'),(105,'tanuj','tm_password'),(104,'tanya','tc_password');
/*!40000 ALTER TABLE `emp_login` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `leaves`
--

DROP TABLE IF EXISTS `leaves`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `leaves` (
  `emp_id` int NOT NULL,
  `leaves_allowed` int NOT NULL,
  `leaves_taken` int NOT NULL,
  `leaves_left` int NOT NULL,
  KEY `emp_id` (`emp_id`),
  CONSTRAINT `leaves_ibfk_1` FOREIGN KEY (`emp_id`) REFERENCES `official` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `leaves`
--

LOCK TABLES `leaves` WRITE;
/*!40000 ALTER TABLE `leaves` DISABLE KEYS */;
INSERT INTO `leaves` VALUES (101,20,7,13),(104,40,21,19),(105,15,5,10);
/*!40000 ALTER TABLE `leaves` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `official`
--

DROP TABLE IF EXISTS `official`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `official` (
  `id` int NOT NULL,
  `name` varchar(255) NOT NULL,
  `join_date` date NOT NULL,
  `designation` varchar(255) NOT NULL,
  `department` varchar(255) NOT NULL,
  `monthly_salary` decimal(9,2) NOT NULL,
  `email` varchar(255) NOT NULL,
  `phone_num` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `official`
--

LOCK TABLES `official` WRITE;
/*!40000 ALTER TABLE `official` DISABLE KEYS */;
INSERT INTO `official` VALUES (101,'Taslim Mohammad','2019-03-20','Officer','Sales',25000.00,'druvin@gmail.com','9263836610'),(104,'Tanya Chawla','2016-03-20','Officer','HR',50000.00,'tanya@gmail.com','9901532367'),(105,'Tanuj Mahajan','2019-03-20','Officer','R&D',75000.00,'tanuj@gmail.com','8804729581'),(120,'Hridoy paul','2025-11-20','ASDC','CSE',1200.00,'DER12asd@gmail.com','01988020941'),(131,'Arim Kahn','2001-04-10','Officer','HR',20000.00,'Arim12@gmail.com','01610226020'),(190,'Banik','2004-09-14','logistic','CSE',20000.00,'Em456Aklim@gmail.com','017109969543'),(200,'Sagor Dev','2006-12-24','ML department','Machine Learning',35000.00,'Sagor121@gmail.com','01617789920');
/*!40000 ALTER TABLE `official` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `salary`
--

DROP TABLE IF EXISTS `salary`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `salary` (
  `emp_id` int NOT NULL,
  `monthly_salary` decimal(9,2) NOT NULL,
  `bonus` decimal(9,2) NOT NULL DEFAULT '0.00',
  `deduction` decimal(9,2) NOT NULL DEFAULT '0.00',
  KEY `emp_id` (`emp_id`),
  CONSTRAINT `salary_ibfk_1` FOREIGN KEY (`emp_id`) REFERENCES `official` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `salary`
--

LOCK TABLES `salary` WRITE;
/*!40000 ALTER TABLE `salary` DISABLE KEYS */;
INSERT INTO `salary` VALUES (101,25000.00,5000.00,0.00),(104,50000.00,2500.00,0.00),(200,20000.00,500.00,0.00);
/*!40000 ALTER TABLE `salary` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-12-15 22:37:12
