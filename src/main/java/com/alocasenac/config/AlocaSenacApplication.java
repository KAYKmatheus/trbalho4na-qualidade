package com.alocasenac.config;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;

@SpringBootApplication(scanBasePackages = "com.alocasenac")
@EntityScan(basePackages = "com.alocasenac.persistencia")
@EnableJpaRepositories(basePackages = "com.alocasenac.persistencia")
public class AlocaSenacApplication {

    public static void main(String[] args) {
        SpringApplication.run(AlocaSenacApplication.class, args);
    }
}