package com.twitter.common.zookeeper;

import java.net.InetSocketAddress;
import java.util.List;
import java.util.Map;

import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Lists;

import org.easymock.Capture;
import org.easymock.IMocksControl;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;

import com.twitter.common.base.Command;
import com.twitter.common.net.pool.DynamicHostSet.HostChangeMonitor;
import com.twitter.common.net.pool.DynamicHostSet.MonitorException;
import com.twitter.common.zookeeper.testing.BaseZooKeeperTest;
import com.twitter.thrift.ServiceInstance;
import com.twitter.thrift.Status;

import static com.twitter.common.testing.EasyMockTest.createCapture;
import static org.easymock.EasyMock.anyObject;
import static org.easymock.EasyMock.capture;
import static org.easymock.EasyMock.createControl;
import static org.easymock.EasyMock.expect;
import static org.easymock.EasyMock.expectLastCall;

/**
 * Tests CompoundServerSet (Tests the composite logic). ServerSetImplTest takes care of testing
 * the actual serverset logic.
 */
public class CompoundServerSetTest extends BaseZooKeeperTest {
  private static final Map<String, InetSocketAddress> AUX_PORTS = ImmutableMap.of();
  private static final ImmutableSet<ServiceInstance> EMPTY_HOSTS = ImmutableSet.of();
  private static final InetSocketAddress END_POINT =
      InetSocketAddress.createUnresolved("foo", 12345);

  private ServerSet.EndpointStatus mockStatus1;
  private ServerSet.EndpointStatus mockStatus2;
  private ServerSet.EndpointStatus mockStatus3;
  private HostChangeMonitor mockMonitor;

  private ServerSet serverSet1;
  private ServerSet serverSet2;
  private ServerSet serverSet3;
  private List<ServerSet> serverSets;
  private CompoundServerSet compoundServerSet;

  private ServiceInstance instance1;
  private ServiceInstance instance2;
  private ServiceInstance instance3;

  private IMocksControl control;

  private void triggerChange(ServiceInstance... hostChanges) {
    mockMonitor.onChange(ImmutableSet.copyOf(hostChanges));
  }

  private void triggerChange(Capture<HostChangeMonitor> capture, ServiceInstance... hostChanges) {
    capture.getValue().onChange(ImmutableSet.copyOf(hostChanges));
  }

  @Before
  public void setUpMocks() throws Exception {
    control = createControl();

    mockMonitor = control.createMock(HostChangeMonitor.class);

    mockStatus1 = control.createMock(ServerSet.EndpointStatus.class);
    mockStatus2 = control.createMock(ServerSet.EndpointStatus.class);
    mockStatus3 = control.createMock(ServerSet.EndpointStatus.class);

    serverSet1 = control.createMock(ServerSet.class);
    serverSet2 = control.createMock(ServerSet.class);
    serverSet3 = control.createMock(ServerSet.class);
    serverSets = Lists.newArrayList(serverSet1, serverSet2, serverSet3);

    instance1 = control.createMock(ServiceInstance.class);
    instance2 = control.createMock(ServiceInstance.class);
    instance3 = control.createMock(ServiceInstance.class);

    compoundServerSet = new CompoundServerSet(serverSets);
  }

  @After
  public void verify() {
    control.verify();
  }

  @Test
  public void testJoin() throws Exception {
    expect(serverSet1.join(END_POINT, AUX_PORTS, Status.ALIVE)).andReturn(mockStatus1);
    expect(serverSet2.join(END_POINT, AUX_PORTS, Status.ALIVE)).andReturn(mockStatus2);
    expect(serverSet3.join(END_POINT, AUX_PORTS, Status.ALIVE)).andReturn(mockStatus3);

    mockStatus1.update(Status.DEAD);
    mockStatus2.update(Status.DEAD);
    mockStatus3.update(Status.DEAD);

    control.replay();

    ServerSet.EndpointStatus status = compoundServerSet.join(END_POINT, AUX_PORTS, Status.ALIVE);
    status.update(Status.DEAD);
  }

  @Test(expected = Group.JoinException.class)
  public void testJoinFailure() throws Exception {
    // Throw exception for the first serverSet join.
    expect(serverSet1.join(END_POINT, AUX_PORTS, Status.ALIVE))
        .andThrow(new Group.JoinException("Group join exception", null));

    control.replay();
    compoundServerSet.join(END_POINT, AUX_PORTS, Status.ALIVE);
  }

  @Test(expected = ServerSet.UpdateException.class)
  public void testStatusUpdateFailure() throws Exception {
    expect(serverSet1.join(END_POINT, AUX_PORTS, Status.ALIVE)).andReturn(mockStatus1);
    expect(serverSet2.join(END_POINT, AUX_PORTS, Status.ALIVE)).andReturn(mockStatus2);
    expect(serverSet3.join(END_POINT, AUX_PORTS, Status.ALIVE)).andReturn(mockStatus3);

    mockStatus1.update(Status.DEAD);
    mockStatus2.update(Status.DEAD);
    expectLastCall().andThrow(new ServerSet.UpdateException("Update exception"));
    mockStatus3.update(Status.DEAD);

    control.replay();

    ServerSet.EndpointStatus status = compoundServerSet.join(END_POINT, AUX_PORTS, Status.ALIVE);
    status.update(Status.DEAD);
  }

  @Test
  public void testMonitor() throws Exception {
    Capture<HostChangeMonitor> set1Capture = createCapture();
    Capture<HostChangeMonitor> set2Capture = createCapture();
    Capture<HostChangeMonitor> set3Capture = createCapture();

    serverSet1.monitor(capture(set1Capture));
    serverSet2.monitor(capture(set2Capture));
    serverSet3.monitor(capture(set3Capture));

    triggerChange(instance1);
    triggerChange(instance1, instance2);
    triggerChange(instance1, instance2, instance3);
    triggerChange(instance1, instance3);
    triggerChange(instance1, instance2, instance3);
    triggerChange(instance3);
    triggerChange();

    control.replay();
    compoundServerSet.monitor(mockMonitor);

    // No new instances.
    triggerChange(set1Capture);
    triggerChange(set2Capture);
    triggerChange(set3Capture);
    // Add one instance from each serverset
    triggerChange(set1Capture, instance1);
    triggerChange(set2Capture, instance2);
    triggerChange(set3Capture, instance3);
    // Remove instance2
    triggerChange(set2Capture);
    // instance1 in both serverset1 and serverset2
    triggerChange(set2Capture, instance1, instance2);
    // Remove instances from serversets.
    triggerChange(set1Capture);
    triggerChange(set2Capture);
    triggerChange(set3Capture);
}

  @Test(expected = MonitorException.class)
  public void testMonitorFailure() throws Exception {
    serverSet1.monitor((HostChangeMonitor<ServiceInstance>) anyObject());
    expectLastCall().andThrow(new MonitorException("Monitor exception", null));

    control.replay();
    compoundServerSet.monitor(mockMonitor);
  }
}
