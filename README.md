# MoFA搜索 （Mofasearch）
GOSIM 超级智能体大赛：构建一个组合搜索引擎
GOSIM Super Agent Hackathon: Building a Composition Search Engine
---
## 简介
### MoFA搜索引擎: 定义

MoFA搜索引擎是一个组合搜索引擎：是一个分布式，去中心化的，智能体驱动的，深层网络集成搜索引擎。它：

1. 不依赖于爬虫
2. 返回实时信息
3. 保护用户隐私
4. 尊重内容提供者的利益
5. 搜索范围可超过搜索引擎数十倍
6. 通过智能体的组合实现的搜索，每个AI开发者都可以出力
   
**MoFA Composition Search Engine: Agentic, Distributed, DeepWeb Metasearch Engine**

### 背景

#### 表层网络 vs. **深层网络**

1. **表层网络（Surface Web）**：
   - 也称为“可见网络”。
   - 这是互联网上可以被搜索引擎（如Google、Bing、Yahoo等）索引的部分，任何人都可以通过标准搜索工具访问。
   - 包括公共网站、新闻文章、社交媒体个人资料、博客和电子商务网站等。
   - 仅占整个互联网的很小一部分，约为4-5%。
2. **深层网络（Deep Web）**：
   - 是互联网中不被搜索引擎索引的部分，不能通过常规搜索查询直接访问。
   - 深层网络包含私人数据库、学术期刊、医疗记录、政府文件、仅限订阅内容、密码保护的网站和内部公司网站。
   - 通常需要登录、订阅或特定的网址才能访问，但不涉及非法或隐藏的内容。
   - 占据了互联网内容的绝大多数，估计约**90%以上**。

两者的关键区别在于是否可以被搜索引擎爬取和有效索引：表层网络的内容是可以被爬取、索引，因此是可搜索的，而深层网络的内容是是动态生成的，或者有意限制的，是不能爬或不让爬的，通常需要在内容提供商的网络门户进行搜索，或得到他们的授权以后，通过直接链接访问。

MoFA搜索引擎使得用户能够更方便地地搜索深层网络。

#### Centralized Search vs. **Decentralized Search**

去中心化的搜索是一种通过分散节点网络搜索信息的方法，而不是依赖像Google或Perplexity这样的集中式实体。与集中式搜索引擎依靠单一组织维护的大型数据库不同，去中心化的搜索引擎将工作负载和数据分散到多个独立节点或用户中。其主要特点和示例如下：

1. **点对点（P2P）架构**：
   - 分布式搜索通常使用点对点（P2P）网络，其中用户既是信息的提供者也是消费者。
   - 数据存储在多个节点上，搜索请求通过一系列节点而非中心服务器进行处理。
   - 例如使用BitTorrent协议的分布式网络，文件在用户设备之间共享。
2. **隐私和控制**：
   - 用户对自己的数据拥有更多控制权，因为没有单一的组织来追踪或收集信息。
   - 分布式搜索能减少对中心化机构的依赖，增强抵御审查和数据操控的能力。
3. **分布式搜索引擎的例子**：
   - **YaCy**：一个开源、去中心化的搜索引擎，用户运行自己的搜索节点并可连接到全球YaCy用户网络，从而形成一个大型的分布式搜索索引。
   - **Presearch**：基于区块链的搜索引擎，通过奖励用户参与，实现数据和隐私的去中心化。
   - **IPFS（星际文件系统）**：虽然不是一个搜索引擎，但IPFS是一个分布式文件系统，允许去中心化的文件存储和检索，为分布式搜索奠定了基础。
4. **优点**：
   - **抗干扰性**：没有单点故障，即使一个节点关闭，其他节点仍然可以处理搜索请求。
   - **隐私保护**：通常没有集中式实体收集用户数据，降低了隐私风险。
   - **减少审查**：内容难以被审查或移除，因为数据分布在多个节点上。
5. **挑战**：
   - **性能和速度**：分布式网络的速度可能比集中式网络慢，尤其是对于复杂的搜索请求。
   - **数据质量**：没有集中索引，保持高质量、相关的搜索结果具有一定难度。
   - **安全性和信任**：分布式系统可能受到恶意节点的威胁，需要机制确保可信的搜索结果。

分布式搜索在隐私保护、抗审查和用户控制方面具有潜力，但与集中式搜索引擎相比，目前在可扩展性和结果质量方面仍面临一些挑战。

#### Search vs. **Metasearch**

“搜索”和“元搜索”指的是两种不同的传统搜索方法，它们的主要区别在于数据的来源和处理方式：

1. **搜索（Search）**：
   - 传统搜索引擎（如Google、Bing）有自己的独立数据库和索引体系，用于存储和整理网页内容。
   - 搜索引擎会主动爬取和索引互联网内容，直接提供由其数据库生成的搜索结果。
   - 优势在于能够提供较为全面、快速、个性化的结果，同时允许用户访问存储在其数据库中的多种类型的信息（如网页、图片、新闻等）。
2. **元搜索（Metasearch）**：
   - 元搜索引擎（如Dogpile、Metacrawler）本身没有自己的数据库，它通过从多个搜索引擎（如Google、Bing、Yahoo等）收集结果，并将这些结果整合后呈现给用户。
   - 它并不直接爬取网页，而是依赖其他搜索引擎的数据，并可能对结果进行一定的过滤、去重或重新排序，以提高结果的多样性和覆盖面。
   - 优势在于能综合不同搜索引擎的结果，避免单一搜索引擎的局限性，并有助于更广泛地覆盖信息。

![Metasearch Engines | SpringerLink](https://media.springernature.com/lw685/springer-static/image/prt%3A978-0-387-39940-9%2F13/MediaObjects/978-0-387-39940-9_13_Part_Fig1-217_HTML.jpg)

#### 区别总结

- **数据来源**：搜索引擎有自己的数据库和索引；元搜索引擎依赖其他搜索引擎的数据。
- **信息质量和丰富度**：搜索引擎的结果可能更定制化，但可能会有所偏向；元搜索提供更广泛的覆盖，但可能缺少个性化。
- **效率和速度**：搜索引擎通常速度更快，直接从其索引中提供结果；元搜索的速度可能较慢，因为它要从多个引擎收集和处理结果。

#### 适用场景

如果希望获得更多元化、广泛覆盖的搜索结果，且避免单一引擎的局限性，则元搜索是一个合适的选择。
## mofa camp/workshop
## mofa academy
## mofa connectors
## mofa interface
## mofa search top infrastructure
