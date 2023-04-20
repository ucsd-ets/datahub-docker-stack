library(testthat)

### IMPORTS HERE
library(randomForest)
library(tidyverse)
library(markdown)
library(lubridate)
library(DT)
library(MASS)
library(RColorBrewer)
library(shiny)
library(Matrix)
library(rvest)

### FUNCTIONS HERE
simple_linear_regression <- function() {
    model <- lm(iris$Sepal.Width ~ iris$Sepal.Length)
    summary(model)
    
    r_sq <- summary(model)$adj.r.squared
    
    # floating point stuff, round to 3 sig figures
    return(signif(r_sq, 3))
    
}

matrix_multiplication <- function() {
    m <- matrix(1:8, nrow=2)
    n <- matrix(8:15, nrow=2)
    
    return(m * n)
}

tidyverse_summarise <- function() {
    library(tidyverse)
    x <- iris %>% group_by(Species) %>% summarise(mean(Sepal.Length))
    x[[2]]
}


### TESTS HERE
test_that(desc="test slr", code = {
    
    result <- simple_linear_regression()
    
    expect_that(result, equals(.00716))
})

test_that(desc="test mat. mult.", code = {
    
    result <- matrix_multiplication()
    
    expect_that(result, equals(matrix(c(8, 18, 30, 44, 60, 78, 98, 120), nrow=2)))
})

test_that(desc="test tidyverse summarise", code = {
    
    result <- tidyverse_summarise()
    
    expect_that(result, equals(c(5.006, 5.936, 6.588)))
})
