package com.twitter.common.testing.runner;

import java.lang.annotation.ElementType;
import java.lang.annotation.Inherited;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * Annotate that a test class must be run in serial. See usage note in {@link JUnitConsoleRunner}.
 * This takes precedence over {@link TestParallel} if a class has both (including inherited).
 *
 * @author: Qicheng Ma
 */
@Retention(RetentionPolicy.RUNTIME)
@Inherited
@Target(ElementType.TYPE)
public @interface TestSerial {
}
