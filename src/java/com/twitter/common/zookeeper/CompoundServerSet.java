package com.twitter.common.zookeeper;

import java.net.InetSocketAddress;
import java.util.List;
import java.util.Map;

import com.google.common.base.Joiner;
import com.google.common.base.Throwables;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Iterables;
import com.google.common.collect.Lists;
import com.google.common.collect.Maps;

import com.twitter.common.base.MorePreconditions;
import com.twitter.thrift.ServiceInstance;
import com.twitter.thrift.Status;

/**
 * A ServerSet that delegates all calls to other ServerSets.
 */
public class CompoundServerSet implements ServerSet {
  private static final Joiner STACK_TRACE_JOINER = Joiner.on('\n');

  private final List<ServerSet> serverSets;
  private final Map<ServerSet, ImmutableSet<ServiceInstance>> instanceCache = Maps.newHashMap();
  private final List<HostChangeMonitor<ServiceInstance>> monitors = Lists.newArrayList();
  private boolean monitoring = false;
  private ImmutableSet<ServiceInstance> allHosts = ImmutableSet.of();

  /**
   * Create new ServerSet from a list of serverSets.
   *
   * @param serverSets serverSets to which the calls will be delegated.
   */
  public CompoundServerSet(Iterable<ServerSet> serverSets) {
    this.serverSets = ImmutableList.copyOf(MorePreconditions.checkNotBlank(serverSets));
  }

  /*
   * If any one of the serverSet throws an exception during respective join, the exception is
   * propagated. Join is successful only if all the joins are successful.
   *
   * NOTE: If an exception occurs during the join, the serverSets in the composite can be in a
   * partially joined state.
   */
  @Override
  public EndpointStatus join(InetSocketAddress endpoint,
      Map<String, InetSocketAddress> additionalEndpoints,
      Status status) throws Group.JoinException, InterruptedException {
    // Get the list of endpoint status from the serverSets.
    ImmutableList.Builder<EndpointStatus> builder = ImmutableList.builder();
    for (ServerSet serverSet : serverSets) {
      builder.add(serverSet.join(endpoint, additionalEndpoints, status));
    }
    final ImmutableList<EndpointStatus> statuses = builder.build();

    return new EndpointStatus() {
      @Override public void update(Status status) throws UpdateException {
        ImmutableList.Builder<String> builder = ImmutableList.builder();
        int errorIdx = 1;
        for (EndpointStatus endpointStatus : statuses) {
          try {
            endpointStatus.update(status);
          } catch (UpdateException exception) {
            builder.add(String.format("[%d] %s", errorIdx++,
                Throwables.getStackTraceAsString(exception)));
          }
        }
        if (errorIdx > 1) {
          throw new UpdateException(
            "One or more ServerSet update failed: " + STACK_TRACE_JOINER.join(builder.build()));
        }
      }
    };
  }

  // Handles changes to the union of hosts.
  private synchronized void handleChange(ServerSet serverSet, ImmutableSet<ServiceInstance> hosts) {
    instanceCache.put(serverSet, hosts);

    // Get the union of hosts.
    ImmutableSet<ServiceInstance> currentHosts =
        ImmutableSet.copyOf(Iterables.concat(instanceCache.values()));

    // Check if the hosts have changed.
    if (!currentHosts.equals(allHosts)) {
      allHosts = currentHosts;

      // Notify the monitors.
      for (HostChangeMonitor<ServiceInstance> monitor : monitors) {
        monitor.onChange(allHosts);
      }
    }
  }

  /**
   * Monitor the CompoundServerSet.
   *
   * @param monitor HostChangeMonitor instance used to monitor host changes.
   * @throws MonitorException
   *
   * If any one of the monitor calls to the underlying serverSet raises a MonitorException, the
   * exception is propagated. The call is successful only if all the monitor calls to the
   * underlying serverSets are successful.
   *
   * NOTE: If an exception occurs during the monitor call, the serverSets in the composite will not
   * be monitored.
   */
  @Override
  public synchronized void monitor(HostChangeMonitor<ServiceInstance> monitor)
      throws MonitorException {
    if (!monitoring) {
      monitoring = true;
      for (final ServerSet serverSet : serverSets) {
        serverSet.monitor(new HostChangeMonitor<ServiceInstance>() {
          @Override public void onChange(ImmutableSet<ServiceInstance> hostSet) {
            handleChange(serverSet, hostSet);
          }
        });
      }
      monitors.add(monitor);
    }
  }
}
