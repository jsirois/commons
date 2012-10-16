// =================================================================================================
// Copyright 2011 Twitter, Inc.
// -------------------------------------------------------------------------------------------------
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this work except in compliance with the License.
// You may obtain a copy of the License in the LICENSE file, or at:
//
//  http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
// =================================================================================================

package com.twitter.common.zookeeper;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.util.List;
import java.util.Map;

import com.google.common.collect.ImmutableMap;
import com.google.common.collect.Lists;

import org.easymock.Capture;
import org.easymock.IExpectationSetters;
import org.junit.Before;
import org.junit.Test;

import com.twitter.common.base.ExceptionalCommand;
import com.twitter.common.testing.EasyMockTest;
import com.twitter.common.zookeeper.Candidate.Leader;
import com.twitter.common.zookeeper.Group.JoinException;
import com.twitter.common.zookeeper.ServerSet.EndpointStatus;
import com.twitter.common.zookeeper.SingletonService.LeaderControl;

import static org.easymock.EasyMock.capture;
import static org.easymock.EasyMock.expect;
import static org.junit.Assert.fail;

/**
 * @author William Farner
 */
public class SingletonServiceTest extends EasyMockTest {
  private static final int PORT_A = 1234;
  private static final int PORT_B = 8080;
  private static final InetSocketAddress PRIMARY_ENDPOINT =
      InetSocketAddress.createUnresolved("foo", PORT_A);
  private static final Map<String, InetSocketAddress> AUX_ENDPOINTS =
      ImmutableMap.of("http-admin", InetSocketAddress.createUnresolved("foo", PORT_B));

  private SingletonService.LeadershipListener listener;
  private ServerSet serverSet;
  private ServerSet.EndpointStatus endpointStatus;
  private Candidate candidate;
  private ExceptionalCommand<Group.JoinException> abdicate;

  private SingletonService service;

  @Before
  @SuppressWarnings("unchecked")
  public void mySetUp() throws IOException {
    listener = createMock(SingletonService.LeadershipListener.class);
    serverSet = createMock(ServerSet.class);
    candidate = createMock(Candidate.class);
    endpointStatus = createMock(ServerSet.EndpointStatus.class);
    abdicate = createMock(ExceptionalCommand.class);

    service = new SingletonService(serverSet, candidate);
  }

  private void newLeader(final String hostName, Capture<Leader> leader) throws Exception {
    service.lead(InetSocketAddress.createUnresolved(hostName, PORT_A),
        ImmutableMap.of("http-admin", InetSocketAddress.createUnresolved(hostName, PORT_B)),
        listener);

    // This actually elects the leader.
    leader.getValue().onElected(abdicate);
  }

  private IExpectationSetters<EndpointStatus> expectJoin() throws Exception {
    return expect(serverSet.join(PRIMARY_ENDPOINT, AUX_ENDPOINTS));
  }

  @Test
  public void testLeadAdvertise() throws Exception {
    Capture<Leader> leaderCapture = createCapture();

    expect(candidate.offerLeadership(capture(leaderCapture))).andReturn(null);
    Capture<LeaderControl> controlCapture = createCapture();
    listener.onLeading(capture(controlCapture));

    expectJoin().andReturn(endpointStatus);
    endpointStatus.leave();
    abdicate.execute();

    control.replay();

    newLeader("foo", leaderCapture);
    controlCapture.getValue().advertise();
    controlCapture.getValue().leave();
  }

  @Test
  public void teatLeadLeaveNoAdvertise() throws Exception {
    Capture<Leader> leaderCapture = createCapture();

    expect(candidate.offerLeadership(capture(leaderCapture))).andReturn(null);
    abdicate.execute();

    Capture<LeaderControl> controlCapture = createCapture();
    listener.onLeading(capture(controlCapture));

    control.replay();

    newLeader("foo", leaderCapture);
    controlCapture.getValue().leave();
  }

  @Test
  public void testLeadJoinFailure() throws Exception {
    Capture<Leader> leaderCapture = new Capture<Leader>();

    expect(candidate.offerLeadership(capture(leaderCapture))).andReturn(null);
    Capture<LeaderControl> controlCapture = createCapture();
    listener.onLeading(capture(controlCapture));

    expectJoin().andThrow(new Group.JoinException("Injected join failure.", new Exception()));
    abdicate.execute();

    control.replay();

    newLeader("foo", leaderCapture);

    try {
      controlCapture.getValue().advertise();
      fail("Join should have failed.");
    } catch (JoinException e) {
      // Expected.
    }

    controlCapture.getValue().leave();
  }

  @Test(expected = IllegalStateException.class)
  public void testMultipleAdvertise() throws Exception {
    Capture<Leader> leaderCapture = createCapture();

    expect(candidate.offerLeadership(capture(leaderCapture))).andReturn(null);
    Capture<LeaderControl> controlCapture = createCapture();
    listener.onLeading(capture(controlCapture));

    expectJoin().andReturn(endpointStatus);

    control.replay();

    newLeader("foo", leaderCapture);
    controlCapture.getValue().advertise();
    controlCapture.getValue().advertise();
  }

  @Test(expected = IllegalStateException.class)
  public void testMultipleLeave() throws Exception {
    Capture<Leader> leaderCapture = createCapture();

    expect(candidate.offerLeadership(capture(leaderCapture))).andReturn(null);
    Capture<LeaderControl> controlCapture = createCapture();
    listener.onLeading(capture(controlCapture));

    expectJoin().andReturn(endpointStatus);
    endpointStatus.leave();
    abdicate.execute();

    control.replay();

    newLeader("foo", leaderCapture);
    controlCapture.getValue().advertise();
    controlCapture.getValue().leave();
    controlCapture.getValue().leave();
  }

  @Test(expected = IllegalStateException.class)
  public void testAdvertiseAfterLeave() throws Exception {
    Capture<Leader> leaderCapture = createCapture();

    expect(candidate.offerLeadership(capture(leaderCapture))).andReturn(null);
    Capture<LeaderControl> controlCapture = createCapture();
    listener.onLeading(capture(controlCapture));

    abdicate.execute();

    control.replay();

    newLeader("foo", leaderCapture);
    controlCapture.getValue().leave();
    controlCapture.getValue().advertise();
  }

  @Test
  public void testLeadMulti() throws Exception {
    List<Capture<Leader>> leaderCaptures = Lists.newArrayList();
    List<Capture<LeaderControl>> leaderControlCaptures = Lists.newArrayList();

    for (int i = 0; i < 5; i++) {
      Capture<Leader> leaderCapture = new Capture<Leader>();
      leaderCaptures.add(leaderCapture);
      Capture<LeaderControl> controlCapture = createCapture();
      leaderControlCaptures.add(controlCapture);

      expect(candidate.offerLeadership(capture(leaderCapture))).andReturn(null);
      listener.onLeading(capture(controlCapture));
      InetSocketAddress primary = InetSocketAddress.createUnresolved("foo" + i, PORT_A);
      Map<String, InetSocketAddress> aux =
          ImmutableMap.of("http-admin", InetSocketAddress.createUnresolved("foo" + i, PORT_B));
      expect(serverSet.join(primary, aux)).andReturn(endpointStatus);
      endpointStatus.leave();
      abdicate.execute();
    }

    control.replay();

    for (int i = 0; i < 5; i++) {
      final String leaderName = "foo" + i;
      newLeader(leaderName, leaderCaptures.get(i));
      leaderControlCaptures.get(i).getValue().advertise();
      leaderControlCaptures.get(i).getValue().leave();
    }
  }
}
