package com.alocasenac.config;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication(scanBasePackages = "com.alocasenac")
public class AlocaSenacApplication {

    public static void main(String[] args) {
        SpringApplication.run(AlocaSenacApplication.class, args);
    }
}