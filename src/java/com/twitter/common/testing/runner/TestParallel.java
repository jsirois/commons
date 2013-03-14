package com.twitter.common.testing.runner;

import java.lang.annotation.ElementType;
import java.lang.annotation.Inherited;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * Annotate that a test class can be run in parallel. See usage note in {@link JUnitConsoleRunner}.
 * {@link TestSerial} takes precedence over this if a class has both (including inherited).
 *
 * @author: Qicheng Ma
 */
@Retention(RetentionPolicy.RUNTIME)
@Inherited
@Target(ElementType.TYPE)
public @interface TestParallel {
}
