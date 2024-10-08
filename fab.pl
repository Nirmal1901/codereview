#!/usr/bin/perl
use strict;
use warnings;

# Simple Perl program to print Fibonacci sequence
sub fibonacci {
    my $n = shift;
    my @fib = (0, 1);
    
    for my $i (2..$n) {
        $fib[$i] = $fib[$i-1] + $fib[$i-2];
    }

    return @fib;
}

# Get first 10 Fibonacci numbers
my @sequence = fibonacci(10);
print "Fibonacci sequence: @sequence\n";
