// Copyright 2024 Intelligent Robotics Lab
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include <fstream>

#include "yaets/tracing.hpp"

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/int32.hpp"

#include <sys/resource.h>
#include <sched.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <cerrno>
#include <cstring>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <thread>
#include <new>
#include <memory>

using namespace std::chrono_literals;
using std::placeholders::_1;


yaets::TraceSession session("strategy_1.log");


void waste_time(rclcpp::Node::SharedPtr node, const rclcpp::Duration & duration)
{
  auto start = node->now();
  while (node->now() - start < duration) {}
}

class ProducerNode : public rclcpp::Node
{
public:
  ProducerNode()
  : Node("producer_node")
  {
    pub_ = create_publisher<std_msgs::msg::Int32>("int_topic", 100);
    timer_ = create_wall_timer(10ms, std::bind(&ProducerNode::timer_callback, this));
  }

  void timer_callback()
  {
    TRACE_EVENT(session);

    waste_time(shared_from_this(), 200us);

    message_.data += 1;
    pub_->publish(message_);
  }

private:
  rclcpp::Publisher<std_msgs::msg::Int32>::SharedPtr pub_;
  rclcpp::TimerBase::SharedPtr timer_;
  std_msgs::msg::Int32 message_;
};

class ConsumerNode : public rclcpp::Node
{
public:
  ConsumerNode()
  : Node("consumer_node")
  {
    sub_ = create_subscription<std_msgs::msg::Int32>(
      "int_topic", 100, std::bind(&ConsumerNode::cb, this, _1));

    timer_ = create_wall_timer(10ms, std::bind(&ConsumerNode::timer_cb, this));
  }

  void cb(const std_msgs::msg::Int32::SharedPtr msg)
  {
    TRACE_EVENT(session);

    waste_time(shared_from_this(), 500us);
  }


  void timer_cb()
  {
    TRACE_EVENT(session);

    waste_time(shared_from_this(), 2ms);
  }

private:
  rclcpp::Subscription<std_msgs::msg::Int32>::SharedPtr sub_;
  rclcpp::TimerBase::SharedPtr timer_;
};

class LoggerNode : public rclcpp::Node
{
public:
  LoggerNode()
  : Node("logger_node")
  {
    sub_ = create_subscription<std_msgs::msg::Int32>(
      "int_topic", 100, std::bind(&LoggerNode::cb, this, _1));

    timer_ = create_wall_timer(10ms, std::bind(&LoggerNode::timer_cb, this));
  }

  void cb(const std_msgs::msg::Int32::SharedPtr msg)
  {
    TRACE_EVENT(session);

    waste_time(shared_from_this(), 500us);
  }


  void timer_cb()
  {
    TRACE_EVENT(session);

    waste_time(shared_from_this(), 2ms);
  }

private:
  rclcpp::Subscription<std_msgs::msg::Int32>::SharedPtr sub_;
  rclcpp::TimerBase::SharedPtr timer_;
};
// SCHED_DEADLINE não tem wrapper na glibc
struct sched_attr_dl {
  uint32_t size;
  uint32_t sched_policy;
  uint64_t sched_flags;
  int32_t  sched_nice;
  uint32_t sched_priority;
  uint64_t sched_runtime;    // ns
  uint64_t sched_deadline;   // ns
  uint64_t sched_period;     // ns
};

void set_fifo_rr(int policy, int prio)       // SCHED_FIFO ou SCHED_RR
{
  sched_param sch{};
  sch.sched_priority = prio;
  if (sched_setscheduler(0, policy, &sch) == -1) {
    throw std::runtime_error{std::string("failed to set scheduler: ") + std::strerror(errno)};
  }
}

void set_other(int nice_value)               // SCHED_OTHER (padrão)
{
  sched_param sch{};
  sch.sched_priority = 0;                    // obrigatório ser 0
  if (sched_setscheduler(0, SCHED_OTHER, &sch) == -1) {
    throw std::runtime_error{std::string("failed to set scheduler: ") + std::strerror(errno)};
  }
  // no Linux, PRIO_PROCESS com tid ajusta só esta thread
  setpriority(PRIO_PROCESS, static_cast<id_t>(syscall(SYS_gettid)), nice_value);
}

void set_deadline(uint64_t runtime_ns, uint64_t deadline_ns, uint64_t period_ns)
{
  sched_attr_dl attr{};
  attr.size = sizeof(attr);
  attr.sched_policy = 6;                     // SCHED_DEADLINE
  attr.sched_runtime = runtime_ns;
  attr.sched_deadline = deadline_ns;
  attr.sched_period = period_ns;
  if (syscall(SYS_sched_setattr, 0, &attr, 0) == -1) {
    throw std::runtime_error{std::string("failed to set deadline: ") + std::strerror(errno)};
  }
}

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);

  auto node_producer = std::make_shared<ProducerNode>();
  auto node_consumer = std::make_shared<ConsumerNode>();
  auto node_logger = std::make_shared<LoggerNode>();

  rclcpp::executors::SingleThreadedExecutor no_rt_executor;
  rclcpp::executors::SingleThreadedExecutor rt_executor;

  no_rt_executor.add_node(node_producer);
  no_rt_executor.add_node(node_logger);
  rt_executor.add_node(node_consumer);

//   auto rt_thread = std::thread(
//     [&]() {
//       sched_param sch;
//       sch.sched_priority = 90;

//       if (sched_setscheduler(0, SCHED_FIFO, &sch) == -1) {
//         throw std::runtime_error{std::string("failed to set scheduler: ") + std::strerror(errno)};
//       }

//       rt_executor.spin();
//   });

auto rt_thread = std::thread(
  [&]() {
    // escolha UMA:
    // set_fifo_rr(SCHED_FIFO, 90);            // o que você tem hoje
    set_fifo_rr(SCHED_RR, 90);                 // round-robin entre threads de mesma prioridade
    // set_other(-5);                          // padrão, com nice (negativo exige privilégio)
    set_deadline(4'000'000, 10'000'000, 10'000'000);   // 4 ms a cada 10 ms

    rt_executor.spin();
  });

//   no_rt_executor.spin();

  rt_thread.join();

  rclcpp::shutdown();
  return 0;
}