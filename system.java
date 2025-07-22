package com.bad.example; 


public class VeryWrongSpringBootApp {

    public static void main(String[] args) {
        System.out.println("I think this is Spring Boot?"); // Not starting Spring
    }

    @GetMapping("/danger") 
    public String dangerZone() {
        return 123; // Returning int instead of String
    }

    @PostMapping("/crash") // No request mapping, wrong annotation without dependencies
    public void crashServer() {
        throw new NullPointerException(); 
    }

 
}
