# 笔记

## 1. STL概论与版本简介

STL提供六大组件，具体可以分为：

1. 容器（container）：其中包含了各种数据结构，如vector、list、deque、set、map等。STL容器是一种类模板。
2. 算法(algorithm)：各种常用算法例如sort、search、copy、erase。从实现的角度来看，STL算法是一种函数模板。
3. 迭代器(iterator)：迭代器是容器和算法之间的“胶合剂”，也称得上是一种“泛型指针”。从实现的角度来看，它是一种重载了`operator*`、`operator++`、`opeator--`、`operator->`等指针操作的类模板。所有的STL容器都附有自己的迭代器，原生指针也是一种迭代器。
4. 仿函数（functor，也称函数对象）：行为类似函数的一种类对象。从实现的角度来看，仿函数是重载了`operator()`的类或者类模板。函数指针可以看作是狭义的仿函数。
5. 适配器(adapter)：一种用来修饰容器、仿函数或迭代器接口的东西，例如STL提供的queue和stack虽然看似容器，但是实际上是容器适配器，因为其底部完全借助deque进行实现。改变仿函数接口的，称为仿函数适配器，其他称呼的方式也一样。
6. 分配器(allocator)：负责空间的分配与管理。从实现的角度来看，分配器是一个实现了动态空间分配与管理及释放的类模板。

本章其他内容非常基础，以几小点概况：

- 恰当的使用临时变量，可以节省内存空间。
- 如果是静态的、整数型（int、long等）的类"常量"，则可以也应该在定义类的内部进行初始化。
- 迭代器的迭代遵循的是左开右闭的区间，也就是`[first, last)`。其迭代范围从`first`到`last-1`。

## 2. 空间分配器

### 2.1 JJ::allocator

`jjalloc.h`:

```cpp
#progma once
/*
`#pragma once` 是一种预处理编译指令，通常放置在C++源文件的开头。它的作用是确保在编译过程中只包含一次特定的头文件，以防止重复包含。这可以提高编译效率并避免潜在的编译错误。

当你在多个源文件中包含同一个头文件时，`#pragma once` 可以确保编译器只处理该头文件一次，而不管它被多次包含。

这是一种用于头文件的常见约定，虽然在不同的编译器和操作系统中可能有其他方式来实现相同的效果，但 `#pragma once` 是一种跨平台且广泛支持的方法。
*/
#ifndef _JJALLOC_
#define _JJALLOC_

#include<new>
#include<cstddef>
#include<cstdlib>
#include<climits>
#include<iostream>

namespace JJ {

	template<class T>
	inline T* _allocate(ptrdiff_t size, T*) {	// 分配内存的函数，分配成功时返回新内存的起始地址
		std::set_new_handler(0);			// 禁用默认的异常处理函数，内存分配失败时不会抛出std::bad_alloc异常
		T* tmp = (T*)(::operator new((size_t)(size * sizeof(T))));	// 尝试分配size * sizeof(T)字节大小的内存
		if (tmp == nullptr) {
			std::cerr << "out of memory" << std::endl;
			exit(1);
		}
		return tmp;
	}

	template<class T>
	inline void _deallocate(T* buffer) {
		::operator delete(buffer);
	}

	template<class T1, class T2>
	inline void _construct(T1* p, const T2& value) {	// 在已分配的内存上构造对象
		new(p) T1(value);		// 使用定位new运算符，指定创建对象的位置
	}

	template<class T>
	inline void _destroy(T* ptr) {	// 销毁创建的对象
		ptr->~T();
	}

	
	template<class T>
	class allocator {
	public:
		typedef T value_type;
		typedef T* pointer;
		typedef const T* const_pointer;
		typedef T& reference;
		typedef const T& const_reference;
		typedef size_t size_type;
		typedef ptrdiff_t difference_type;

		allocator() = default;

		template<class U>
		allocator(const allocator<U>&) {}

		//hint used for locality
		pointer allocate(size_type n, const void* hint = 0) {
			return _allocate((difference_type)n, (pointer)0);
		}

		void deallocate(pointer p, size_type n) {
			_deallocate(p);
		}

		void construct(pointer p, const T& value) {
			_construct(p, value);
		}

		void destroy(pointer p) {
			_destroy(p);
		}

		pointer address(reference x) {
			return (pointer)&x;
		}

		const_pointer const_address(const_reference x) {
			return (const_pointer)&x;
		}

		size_type max_size() const {
			return size_type(UINT_MAX / sizeof(T));
		}
	};
}
#endif _JJALLOC_
```

`2jjalloc.cpp`:

```cpp
#include "jjalloc.h"
#include<vector>
#include<iostream>
using namespace std;

int main() {
	int ia[5] = {0,1,2,3,4};

	vector<int, JJ::allocator<int>> iv(ia, ia + 5);
	for (auto& i : iv) {
		cout << i << " ";
	}
	cout << endl;
	return 0;
}
```

这里贴出代码的原因是在初次编写这段代码的过程中遇到了一些问题，因此做笔记写出原因，后续如果没有遇到特别大的问题，则仅附上书页或文件名。

首先，在`jjalloc.h`的`allocator`类中包含如下代码（书上包含，笔记中贴出的是正确代码）：

```cpp
template<class U>
struct rebind{
	typedef allocator<U> other;
};
```

最初我没有修改这段代码时，当我在`2jjalloc.cpp`中编译代码时，代码无法通过编译并提示：“不存在从`allocator<int>到allocator<U>的转换`”，通常这样的错误都出现在没有定义相应的拷贝操作的情况下。

但是，之前学过的知识告诉我，如果我们没有编写自己的构造函数，则编译器会为我们默认生成，上面的代码也可看出我们的确没有定义任何构造函数。因此我一直找不到错误。

然而，我在未修改任何代码的情况下将这段代码放到洛谷的在线IDE中运行时，可以正常编译并输出结果。也就是说问题无非出现在编译器使用的C++版本或者某个选项导致的编译结果不同（具体什么原因，暂时不得而知）。

后续我将书上的代码删除，并修改为这段代码：

```cpp
allocator() = default;

template<class U>
allocator(const allocator<U>&) {}
```

于是可以在vs2022中正常编译运行了。

值得注意的一件事是，我们显式定义了我们的拷贝构造函数（即使没有做出任何操作），提供了从任何类型的`allocator<U>`到`allocator<T>`的转换，因此之前提示的错误不再出现了。

还有一个插曲就是，一开始我并没有写出：`allocator() = default;`，因为我期待编译器会为我生成默认的构造函数。

但是需要注意的是:<font color="red">编译器只有在我们没有定义任何的默认构造函数时才会为我们生成，也就是说如果我们自己自定义了拷贝构造函数（从形式上来看它就像一个普通的构造函数），编译器就不再为我们生成默认的构造函数了。而如果要将`allocator`应用于STL容器，则需要提供默认的无参构造函数，因此我们指定`=default`来要求编译器生成。</font>

### 2.2 SGI版本的STL空间分配器

在VC或CB系列的版本中，分配器的标准写法为：

```cpp
vector<int, std::allocator<int>> iv;
```

而在SGI中：

```cpp
vector<int, std::alloc> iv;
```

#### 2.2.1 SGI的标准空间分配器，std::allocator

代码在书中P48.

#### 2.2.2 SGI特殊的空间分配器，std::alloc

一般来说，我们通过这样的方式完成C++的内存分配与回收：

```cpp
class Foo{...};
Foo *f = new Foo;
delete f;
```

这里我们使用了`new`和`delete`关键字来完成内存管理，但是实际上它经历了这么几个阶段:

1. new操作符调用`::operator new()`函数，它是C++标准的全局内存分配函数，实际由它分配内存。
2. 内存分配完成后，new操作符继续调用Foo的构造函数，完成对象的构造。

`delete`关键字做了类似的事，只不过顺序相反，先完成对象的析构再释放内存。

为了精密分工，`STL allocator`将这两阶段的操作区分开来（正如我们在2.1节展示的代码一样）。内存分配及回收分别由`::opetator new`和`::operator delete`负责，而对象的构造和析构则由`::construct()`和`::destroy()`负责。

#### 2.2.3 construct()和destroy()

代码在书中P51。

这部分代码主要介绍了`stl_construct.h`的部分核心内容。使用定位new运算符在已分配好的内存上构建对象，在销毁对象的过程中进行了一些提升效率的操作。在销毁某个对象时，判断该对象类型的析构函数是否是"平凡的"，对于一个具有平凡析构函数的类对象而言，它不需要执行任何的内存清理操作，因此如果我们不再使用它了，下次在它所在的内存空间中直接使用定位`new`运算符来创建对象（或别的操作）覆盖它即可。

而如果一个对象类型的析构函数是“不平凡”的，那我们就只能老老实实的调用它的析构函数了，这样才能确保内存被正确的释放。

> 在 C++ 中，一个“trivial destructor”（平凡析构函数）是一个在对象销毁时不执行任何额外操作的析构函数。具体来说，平凡析构函数有以下特点：
>
> 1. 它不显式定义。
> 2. 如果类没有显式定义析构函数，编译器会生成一个默认的平凡析构函数。
> 3. 平凡析构函数不会调用任何基类或成员对象的析构函数。
> 4. 它不会释放动态分配的内存，不会关闭文件，不会执行其他清理操作。
>
> 这就意味着对于包含内置数据类型（如 `int`、`double`）或者内部对象（它们自己也有平凡析构函数）的简单类，通常不需要显式定义析构函数，因为编译器生成的默认析构函数足够。
>
> 然而，当类包含指向动态分配内存的指针、打开文件或有其他需要在对象销毁时进行清理的资源时，你可能需要显式定义析构函数来确保这些资源被正确释放，以避免内存泄漏和资源泄漏。
>
> 要注意的是，C++11 引入了 `= default` 和 `= delete` 的语法，允许你显式指定一个析构函数是否平凡，以及是否可访问。这可以提供更精确的控制。
>
> 这里额外提一点，在析构函数中使用`std::cout`也会被视为“执行了额外操作”。

#### 2.2.4 std::alloc

这部分比较复杂，我尝试进行一点一点的解释。

首先，这部分过程（即内存的分配与释放）发生在上一节的`construct()`和`destroy()`之前（内存释放当然在这过程之后）。

整个内存的配置的设计主要考虑如下几点:

- 向系统的内存堆要求得到内存
- 考虑多线程的状态
- 考虑内存不足时的措施
- 考虑过多“小块内存”造成的内存碎片问题。

其中书中主要涉及到了除多线程以外的所有点。

内存配置的基本操作就是`::operator new()`和`::operator() delete`，它们的地位就相当于`malloc()`和`free()`。

考虑小块内存带来的内存碎片的问题，SGI设计中使用了双层内存分配器。第一层内存分配器直接使用`malloc()`和`free()`，而第二层内存分配器根据不同的情况采用相应的策略：如果分配区块大小大于128字节，则认为分配了一个较大的区块，直接使用第一层的内存分配器。如果分配区块大小小于128字节，则采用复杂的内存池整理的方式。

> 在 SGI STL（史丹佛标准模板库）中，`__USE_MALLOC` 宏的定义通常用于控制 STL 中的内存分配策略。具体来说，如果 `__USE_MALLOC` 宏被定义，SGI STL 将使用 `malloc` 和 `free` 等标准 C 函数来执行内存分配和释放，而不是使用 C++ 中的 `new` 和 `delete` 运算符。这可以用于切换 STL 的内存管理方式。
>
> `__USE_MALLOC` 宏的定义可能会影响 STL 中的内存分配性能和行为。使用 `malloc` 和 `free` 可能会更快，但与 C++ 内存管理兼容性较差。如果你需要使用 STL，可以根据你的具体需求和性能要求来决定是否定义 `__USE_MALLOC` 宏。
>
> 请注意，SGI STL 是一个较早的 STL 实现，而现代的 C++ 标准库在内存管理方面进行了改进，使用 C++ 标准库通常是更好的选择，特别是在新的 C++ 项目中。

<font color="red">注意，默认情况下SGI STL并未定义`__USE_MALLOC`。</font>

也就是说，默认情况下仍然使用`new`和`delete`进行内存配置。但是无论使用哪种方式，SGI都为其包装了一个接口：

```cpp
template<class T, class Alloc>
class simple_alloc{
	public:
		static T* allocate(size_t n){
			return 0==n ? 0 : (T*) Alloc::allocate(n * sizeof(T));
		}
		static T* deallocate(void){
			return (T*) Alloc::allocate(sizeof(T));
		}
		static void deallocate(T *p, size_t n){
			if(0 != n){
				Alloc::deallocate(p, n * sizeof(T));
			}
		}
		static void deallocate(T* p){
			Alloc::deallocate(p, sizeof(T));
		}
}
```

上述类只是定义了一个简单的接口模板类，具体调用的仍然是实现该接口的实体类分配器对象。

#### 2.2.5 第一层配置器__malloc_alloc_template 剖析

代码在P56。这段代码其实很好理解，我简单解释它做了些什么。

首先它定义了默认的内存分配函数，在默认分配内存时如果分配失败，则会调用处理内存不足的函数。此外，如果需要重新分配内存，则也进行相同的操作。

用于处理内存不足的函数(`oom_malloc`)中定义了一个函数指针，该指针用于接收处理内存异常的`new-handler`函数（正如Effective C++的条款49提到的，该函数用于处理具体的内存配置问题，例如释放内存或者别的操作）。接着，在`oom_malloc`函数中会调用一个死循环，循环中会不断调用`new-handler`函数然后尝试分配内存，直到内存被成功分配返回新内存的起始地址，或者因为没有处理内存问题的`new-handler`抛出`BAD_ALLOC`异常。

#### 2.2.6. 第二层配置器__default_alloc_template 剖析

正如书中所言，如果用户在分配内存的过程中尝试多次分配了小块内存，则直接使用第一层配置器进行内存分配可能会带来内存碎片的问题。此外，多次要求系统去分配内存也会带来额外的负担。

第二层配置器针对上述问题做出了一些措施。如果要求分配的大小大于`128bytes`，那么就移交第一层配置器进行处理（说明申请的不是小块内存，不容易产生内存碎片等问题，因此第一层配置器足以处理）。反之，要求分配大小小于`128bytes`时，则移交`Memory Pool`进行处理。

`Memory Pool`究竟是如何管理内存的？我将尝试用自己的方式进行解释。

首先，这种方法又被称为次级配置：每次配置一大块内存，并且维护与之对应的自由链表。下次若有小块的内存申请，则直接从自由链表中拨出内存分配，如果释放了小块内存，则同样将其归还到自由链表中。

此外，为了方便管理，第二层配置器还会将任何小额区块的内存申请数量与8对齐（例如要求`30bytes`，实际分配`32bytes`）。

第二层配置器总共维护了16个自由链表，它们各自维护的大小分别从8、16、24、...、128，自由链表的节点结构如下：

```cpp
union obj{
	union obj* free_list_link;
	char client_data[1];
}
```

<font color="red">下述内容详细代码在P61，这里按理解进行筛选讲解。</font>

当我们实现一个第二层配置器时，首先我们需要进行上述所说的内存对齐（这与机器有关，32位机器上使用4字节对齐，64位机器上则时8字节对齐）：

```cpp
enum {__ALIGN = 8}; // 小块内存对齐的标准
enum {__MAX_BYTES = 128};	//	小块内存的上限
enum {__NFREELISTS = __MAX_BYTES / __ALIGN};	//	维护的自由链表个数
```

已知了自由链表的个数，我们就可以定义指针数组，每个元素都是一个自由链表的头节点，分别指向了不同大小的内存块：

```cpp
static obj* volatile free_list[__NFREELISTS];
```

例如，`free_list[0]`就可以表示为一个自由链表的头节点，它负责维护一个"每个节点均为8字节大小"的自由链表，而`free_list[2]`就可以表示一个"每个节点均为24字节大小"的自由链表，以此类推。

据此，我们可以使用该函数来计算每次申请内存时，实际分配的字节数：

```cpp
static size_t ROUND_UP(size_t bytes){
	return (((bytes) + __ALIGN - 1) & ~(__ALIGN - 1));
}
```

> 这个函数的功能是将给定的 `bytes` 向上舍入到最接近的较大的、满足特定对齐要求的值，并返回结果。
>
> 具体来说，函数的功能如下：
>
> 1. `(bytes) + __ALIGN - 1`：首先，将 `bytes` 与特定对齐值 `__ALIGN` 相加，并减去1。这一步的目的是将 `bytes` 向上舍入到最接近的较大的满足对齐要求的值。
> 2. `& ~(__ALIGN - 1)`：接下来，使用位掩码 `~(__ALIGN - 1)` 对结果进行按位与运算。位掩码的目的是将结果的最后 `__ALIGN` 位设置为零，从而确保对齐要求得到满足。这将确保 `bytes` 被向上对齐到 `__ALIGN` 的倍数。
> 3. 最终，函数返回向上舍入的结果，以满足特定的对齐要求。

已知了我们需要的内存大小，我们就可以据此知道去哪个自由链表中申请合适大小的内存了：

```cpp
static size_t FREELIST_INDEX(size_t bytes){
	return ((bytes + __ALIGN - 1) / __ALIGN - 1);
}
```

这将计算我们所需要的内存大小在第几个自由链表中进行申请。

特别说明的是，为什么自由链表的节点采用`union`？这是因为在一个`union`中，不论包含了多少个成员，它们同时只能存在一个有效值。且所有成员的起始地址相同。而在作为自由链表的节点时，未进行分配时我们使用`free_list_link`指向另一个节点形成链表。而当我们取出了一个节点时，我们就不再使用它的`free_list_link`了，表明这个节点已经分配给用户使用。

> 你的描述关于`Memory Pool`和第二层配置器是非常清晰的。以下是我对你描述的几点补充和建议：
>
> 1. **次级配置器的目的**：你提到了次级配置器的工作原理，但可以进一步强调它的目的是为了提高小块内存的分配和回收效率。传统的内存分配器可能在处理大量小块内存请求时效率不高，而次级配置器通过预先分配大块内存并维护自由链表来解决这个问题。
>
> 2. **对齐的重要性**：你提到了内存对齐，这是非常重要的。对齐可以确保内存访问的速度和效率，特别是在某些硬件平台上，未对齐的内存访问可能会导致性能下降或其他问题。
>
> 3. **`union`的使用**：你对`union`的描述是正确的。使用`union`确实是为了在不同的情境下复用同一块内存，既可以作为链表节点，也可以作为用户数据存储。这种设计是为了节省内存和提高效率。
>
> 4. **代码注释**：你的代码注释非常有助于理解代码的功能，特别是对于`ROUND_UP`和`FREELIST_INDEX`函数的解释。这样的注释可以帮助读者更快地理解代码的目的和工作原理。
>
> 总的来说，你的描述是非常详细和准确的，为读者提供了一个清晰的视角来理解`Memory Pool`和第二层配置器的工作原理。

#### 2.2.7 空间配置函数allocate()

这部分实际上就是刚才描述第二层分配器的具体实现，具体代码在P62。

此函数首先判断要求的内存大小，大于128字节则交给第一层配置器调用。小于128字节则计算用于分配内存的自由链表的下标。如果对应的链表中已经没有可用节点（没有合适的内存了），则调用`refill(ROUND_UP(n))`函数来重新填充对应的自由链表（refill的实现等会说）。如果节点可用，则取出该节点，并将指针指向该链表中的下一个节点（有点像头插法，但是是“头取”）。

```cpp
static void * allocate(size_t n){
	obj * volatile * my_free_list;
	obj * result;
	
	if(n > (size_t) __MAX_BYTES){
		return (malloc_alloc::allocate(n));
	}
	my_free_list = free_list + FREELIST_INDEX(n);
	result = *my_free_list;
	if(return == nullptr){
		void *r = refill(ROUND_UP(n));
		return r;
	}
	*my_free_list = result->free_list_link;
	return result;
}
```

#### 2.2.8 空间释放函数deallocate()

与`allocate()`类似，回收时它遵循着同样的原则。如果回收的内存块大于128字节，则交由第一层配置器回收，否则将其交还给对应的`free_list`。

```cpp
static void deallocate(void *p, size_t n){
	obj *q = (obj *) p;
	obj * volatile * my_free_list;
	if(n > (size_t) __MAX_BYTES){
		malloc_alloc::deallocate(p, n);
		return;
	}
	my_free_list = free_list + FREELIST_INDEX(n);
	q->free_list_link = *my_free_list;
	*my_free_list = q;	//这下真的是头插法了。
}
```

#### 2.2.9 重新填充free lists

在我们上面所提到的`allocate()`函数中，当自由链表中已经没有可用的节点时，我们会尝试重新填充该自由链表并分配内存给用户，这部分依靠我们的`refill(size_t n)`实现。

`refill`函数将从内存池中，经由`chunk_alloc`函数来取得20个新节点。如果内存池中没有 20 * 每个节点大小 的内存，则获得的节点数可能小于20：

```cpp
//注意，上述allocate中调用该函数时嵌套调用了ROUND_UP函数，因此n是一个8字节对齐的数字。
void * __default_alloc_template<threads, inst>::refill(size_t n){
	int nobjs = 20;		// 默认取得20个节点
	//尝试取得nobjs个大小为n的节点
	char * chunk = chunk_alloc(n, nobjs);	// 这里的第二个参数传递的是引用，由它返回实际取得的节点数量。
	obj * volatile * my_free_list;
	obj * result;
	obj * current_obj, *next_obj;
	int i;
	
	//如果chunk_alloc只得到了一个内存块，那么该内存块交给用户使用，free_list不会得到新的节点。
	if(nobjs == 1){
		return chunk;
	}
	//否则调整free_list来容纳新的节点
	my_free_list = free_list + FREELIST_INDEX(n);
	
	result = (obj *)chunk;	// 得到了nobjs(nobjs > 1)个节点，将第1个节点返回给用户。
	*my_free_list = next_obj = (obj *)(chunk + n);	//	注意chunk在声明时声明为char *类型，因此偏移n实际上就是偏移n个字节，即正好一个节点的大小。偏移后的地址就是free_list新得到的第一个节点的起始地址。
	for(i = 1;; i++){	// 循环将新的节点们链接起来，因为第一个节点要返回给用户，因此i从1开始。
		current_obj = next_obj;
		next_obj = (obj *)((char *)next_obj + n);	// 与上面的chunk同理
		if(nobjs - 1 == i){
			current_obj->free_list_link = nullptr;
			break;
		}else{
			current_obj->free_list_link = next_obj;
		}
	}
	return result;
}
```

#### 2.2.10 内存池

内存池的主要功能是经由`chunk_alloc`分配内存给`free_list`使用。这部分代码较长，在书上P66~P68。

下面简单叙述`chunk_alloc`的功能：

首先，我们检查内存池的剩余空间，如果完全满足需要（n * nobjs个字节），那么直接分配。

如果不能满足(n * nobjs)，但是可以分配至少1个n字节大小的内存，那么就分配尽可能多（1或1以上）个n字节大小的内存。

如果连一个n字节大小的内存都不够，则将内存池中剩下的内存尽可能分配给自由链表（比如还剩31字节，则分配给24字节的自由链表，剩下7字节则浪费了）。然后向系统堆申请新的内存空间用于内存池。

如果堆中不够内存，`malloc`失败，则从<font color="red">所有大于等于我们需要字节数的自由链表中</font>检查是否有可用的节点，如果有可用的节点，则将其起始地址和结束地址标记为内存池的可用地址起点和终点（相当于将这个节点归还到内存池），并让自由链表指向下一个节点。然后，我们递归的调用`chunk_alloc`，由于`nobjs`是引用传递，我们可以在递归调用中正确的得到究竟成功分配了几个`n`字节大小的内存。

> 举个例子，假设我们申请了64bytes的内存（注意当`chunk_alloc`函数调用时，需要的字节数已经进行了8字节对齐）。那么堆中内存不够时会检查所有每个节点大小大于等于64字节的自由链表。假设我们在128bytes的自由链表中找到了一个可用节点，那么就会将其归还到内存池中以供使用。
>
> 一个小小的问题就是我们归还得到的节点可能比我们需求的大，就像刚才这个例子一样，128bytes实际上足够申请2个64bytes的空间了。如果碰到极端一点的情况（需求大小为8bytes但是实际上只有128bytes链表有可用节点），那么我们自然不可能返回仅仅一个(`nobjs=1`)节点给用户。
>
> 实际上当节点（注意是大于等于需要字节数的节点）被内存池回收时，其实也就满足了上述"至少1个n字节大小的内存"的情况，因此我们通过递归调用`chunk_alloc`函数再次要求内存，此时一定能满足上面"完全满足"或者"至少1个"的情况，`nobjs`将会是一个`[1, 20]`范围内的整数。

最后的情况是，如果`malloc`失败，而且也无法回收任何节点到内存池中了。内存池最后会尝试调用第一层配置器来尽最后一点努力。这将导致抛出异常，或者意外的情况得到改善（也就是说，调用看看第一层配置器会不会有什么补救措施）。假如抛出了异常那么函数调用也就结束了，如果真的分配到了内存，那么就标记好内存池新的起始地址和结束地址，接着继续递归调用`chunk_alloc`函数来修正`nobjs`。

### 2.3 内存处理基本工具

STL定义了五个全局函数，作用于未初始化的空间上。之前我们看到了`construct()`和`destroy()`，它们分别对应着对象的构造和析构（功能就是申请内存和决定析构函数是否平凡来视情况调用析构函数）。剩余的三个函数分别是`uninitialized_copy()`、`uninitialized_fill()`以及`uninitialized_fill_n()`。

#### 2.3.1 uninitialized_copy

这一函数的函数原型是:

```cpp
template<class InputIterator, class ForwardIterator>
ForwardIterator uninitialized_copy(InputIterator first, InputIterator last, ForwardIterator result);
```

该函数的作用在于将内存的配置和对象的构造行为分离。如果作为输出容器的[result, result + (last - first)]范围内的迭代器都指向未初始化的区域，则该函数会将输入迭代器范围内的对象调用拷贝构造函数复制到输出迭代器中。具体来说，针对输入范围内的每个迭代器`i`，该函数的调用类似:

```cpp
construct(&*(result + (i - first)), *i); // 第一个参数指定在哪个地址构造对象，第二个参数是对象的值
```

> `uninitialized_copy` 是一个C++标准库算法，用于将一个范围内的元素从一个输入范围（例如数组或容器）复制到目标范围，目标范围通常是另一个容器，但必须是未初始化的。
>
> 具体来说，`uninitialized_copy` 的作用如下：
>
> 1. 分配目标范围的内存：首先，它会为目标范围分配足够的内存，以容纳输入范围中的元素。这意味着它会使用分配器来分配内存，以便进行元素复制。
>
> 2. 复制元素：然后，它会从输入范围中复制元素到目标范围中。这通常涉及到对每个元素进行拷贝构造（调用元素类型的拷贝构造函数）。
>
> 3. 返回目标范围的结束迭代器：最后，它返回一个指向目标范围的结束位置的迭代器。
>
> 需要注意的是，`uninitialized_copy` 是用于在未初始化的内存范围中复制元素，而不是用于已初始化的容器。这个算法通常在需要在已分配的内存中复制元素，但不想初始化这些元素时使用。例如，在构建容器时，可以使用 `uninitialized_copy` 将元素从一个容器复制到另一个已分配但未初始化的容器中，然后在需要时手动初始化这些元素。
>
> 请注意，`uninitialized_copy` 在C++标准库的 `<memory>` 头文件中声明，通常与其他未初始化复制算法一起使用。

<font color="red">C++标准要求`uninitialized_copy()`必须具有`commit or rollback`语意，意思就是要么”构造出迭代器范围内所有元素“，要么（当任意对象构造失败时）不构造任何对象，即使已经构造的对象也必须析构。</font>

#### 2.3.2 uninitiated_fill

该函数原型为:

```cpp
template<class ForwardIterator, class T>
void uninitialized_fill(ForwardIterator first, ForwardIterator last, const T& x);
```

与`uninitiated_copy`类似，它的作用同样是将内存的配置与对象的构造分离，同时在某个未初始化的迭代器范围内调用拷贝构造函数构造对象。

具体来说，针对输入范围内的每个迭代器`i`，调用:

```cpp
construct(&*(i), x);
```

<font color="red">与`uninitialized_copy()`一样，它要么产出所有必要元素，要么不产出任何元素。如果有任何拷贝构造函数抛出异常，它必须将已经产生的对象析构。</font>

#### 2.3.3 uninitialized_fill_n

函数原型为:

```cpp
template<class ForwardIterator, class Size, class T>
ForwardIterator uninitialized_fill_n(ForwardIterator first, Size n, const T& x);
```

和上述类似，只不过是在`[first, first + n)`的范围内构造对象。

<font color="red">它也具有`commit or rollback`语意。</font>

 #### 三个函数的具体实现

这三个函数的实现大差不差，具体内容在书中P72。这里给出大概解释。

首先必须了解一个概念：

`POD`，意指`Plain Old Data`，也就是标量类型或传统的`C struct`类型。这些类型可以认为具有**平凡的**构造、析构、拷贝构造、拷贝赋值函数。

首先，执行这些函数时。首先都会通过`value_type()`得到参数中对象的具体类型，并依据`__type_traits`判断其是否为`POD`类型。

如果是`POD`类型，那么会经由一个函数转调用，将实际操作交给高阶函数执行，提高运行效率。

如果不是`POD`类型，那么就只能通过循环`construct(&*i, x)`这样的形式逐个构造复制对象。

三个函数的操作都类似，只是根据参数不同调用不同的函数而已。

值得额外一提的就是`char *`和`wchar_t *`，可以直接采用`memmove()`函数（直接移动内存内容）来执行复制行为，因此SGI为这两种类型设计了特化版本（代码在书中P75）。

> **<font color="red">question:  </font>**SGI中实现了uninitialized_copy、uninitiated_fill、uninitialized_fill_n等函数，这三个函数的具体实现大差不差。基本流程大概是判断参数类型，根据参数是否为POD类型决定调用高阶函数进行复制还是循环进行拷贝构造等。但是我听说它为char *和wchar_t*这两个类型实现了特化版本，当参数类型为二者之一时，直接在特化版本中调用memmove函数进行复制，为什么这两个类型可以这么做？
>
> <font color="green">**answer:** </font>SGI STL (Standard Template Library) 中为 `char*` 和 `wchar_t*` 实现特化版本的原因涉及到这两种类型的特殊性质。 
>
> 1. **`char*` 和 `wchar_t*` 是原始数据类型的指针**：`char*` 是指向字符（通常是字节）的指针，而 `wchar_t*` 是宽字符（通常用于多字节字符编码）的指针。这两种指针通常用于处理原始数据，而不是对象，因此不需要进行对象的构造和析构。对于这种原始数据，`memmove` 函数可以更有效地进行内存复制，因为它直接操作内存的字节而无需进行构造和析构。这也使得 `char*` 和 `wchar_t*` 适合进行特化处理。
>
> 2. **性能考虑**：在处理大量数据时，对于 `char*` 和 `wchar_t*` 进行特化处理可以提高性能，因为直接调用 `memmove` 是一种高效的内存复制操作。STL 的设计者可能认为对于这两种特殊情况，使用 `memmove` 会更快，因此实现了特化版本以提高性能。
>
> 综上所述，特化 `char*` 和 `wchar_t*` 类型的处理是出于性能和效率的考虑，因为这两种类型通常用于处理原始数据，而不需要涉及对象的构造和析构。通过直接使用 `memmove` 来处理内存复制，可以减少不必要的开销并提高性能。这种特化处理充分利用了这两种指针类型的特殊性质。
>
> <font color="red">**question: **</font>但是如果参数是POD类型（例如int），不是也同样不需要进行对象的构造和析构吗？
>
> <font color="green">**answer:** </font>您提出的观点是正确的，如果参数是POD（Plain Old Data，普通旧数据）类型，就不需要进行对象的构造和析构，与 `char*` 和 `wchar_t*` 类型类似，它们也适合使用内存复制操作。所以，您的疑问很合理：为什么对于 `POD` 类型没有类似于 `char*` 和 `wchar_t*` 那样的特化版本？
>
> 这是因为 C++ 标准库中的算法和容器设计的一个关键原则是泛型性。STL 尝试保持算法的泛型性，以便它们可以适用于各种不同类型的数据，包括 `POD` 类型和用户自定义类型。在泛型算法中，不假定数据的特定特性，因此默认情况下进行构造和析构操作，以支持任何可能需要这些操作的类型。
>
> 对于 `char*` 和 `wchar_t*` 类型，它们被视为特殊情况，因为它们通常用于处理原始数据，这不需要构造和析构操作。因此，STL 中的某些实现可能会为这些类型提供特化版本，以提高性能。
>
> 尽管如此，STL 的泛型性意味着它的算法通常会为大多数类型工作，包括 `POD` 类型。如果性能是一个问题，可以考虑自定义算法，或者根据具体情况手动使用 `memmove` 等操作来提高效率。
>
> <font color="red">**question:**  </font>换句话说，为什么它并没有为int、char这样的POD类型去设计特化版本？
>
> **<font color="green">answer: </font>**您提出的问题很有意义，为什么STL没有为 `int`、`char` 这样的POD（Plain Old Data）类型设计特化版本，以提高性能呢？这实际上是STL的设计选择之一，它涉及到权衡和通用性考虑。
>
> STL（标准模板库）的设计注重通用性，它的目标之一是为各种数据类型提供一致和通用的接口。虽然 `int`、`char` 等POD类型在内存复制时不需要构造和析构操作，但STL的设计思想是将算法和容器的操作一致地应用于所有类型，无论是内置数据类型还是用户自定义类型。这种一致性使得STL非常灵活，并且对于不同类型的数据都能提供一致的接口。
>
> STL通过在算法中使用构造和析构操作来确保通用性，这使得算法可以适用于任何数据类型，包括自定义类型。虽然对于POD类型这些操作可能是多余的，但它们不会引入重大性能损失，因为编译器通常会进行很多优化。
>
> 从STL设计的角度来看，维持通用性是一种权衡，牺牲了一些性能以获得更广泛的适用性。如果性能是首要考虑因素，可以考虑手动使用 `memmove` 等操作来提高效率，或者自定义算法以适应特定类型的需求。但STL的目标是提供一致的通用接口，使得其算法和容器适用于多种类型，这是其设计原则之一。

## 3. 迭代器概念与traits编程技术

迭代器模式的定义：提供一种方法，使之能够依序访问某个容器所含的各个元素，而又无需暴露该容器的内部表达方式。

### 3.1 设计迭代器的思维

为什么要设计迭代器？这是因为STL致力于将数据容器和算法分开，彼此独立设计，最后采用某样东西将它们汇聚在一起来实现功能，某样东西就是迭代器。

### 3.2 迭代器是一种智能指针

正如标题中所提到的，迭代器与指针有着一些相似之处，比如都可以通过解引用运算符`*`得到指向对象的值，通过`->`运算符来得到对象的某个属性。

本节内容中给出了一个关于链表的例子，这个例子暴露出的问题是：当我们创建了一个`List`的迭代器`ListIter`时，我们不得不暴露了`List`的组成部分之一的`ListItem`。同时，为了实现`ListIter`，我们也不得不在`ListIter`类中直接调用`ListItem`的成员函数。<font color="red">这就意味着如果要实现`ListIter`就必须对`ListItem`有充分的了解。</font>

基于这样的原因，我们干脆不如将`ListIter`的开发任务同样交给`ListItem`的制造者，这样也可以保证使用者无需关心实现细节。

### 3.3 迭代器的相应类型

本节提出了一个问题：在算法中用到迭代器时，很可能要用到其相应的类型（考虑对于一个包含若干个元素的vector，假设我们实现了一个swap函数，在某个范围内逐个交换元素，那么在swap函数内就需要一个临时变量来保存交换过程中的某个元素）。

但是C++中并没有所谓的`typeof`，即使是支持了RTTI性质的`typeid`，虽然它可以获得类型的名称，但是该名称并不能用作变量声明（因为`typeid()`返回的就是一个`std::type_info`类型的对象，对象怎么能做类型声明呢）。

那么如何实现获得迭代器所指向对象的类型呢？答案就是使用函数模板的参数推导功能:

```cpp
template<class I, class T>
void func_impl(I iter, T val){
	T tmp;	// T 就是迭代器iter指向的元素的实际类型
	//功能实现
}
template<class I>
void func(I iter){
	func_impl(iter, *iter);
}
```

### 3.4 Traits编程技术

上述找到迭代器指向元素类型的方法已经能够较为不错的工作了，但是仍然有一个问题：

<font color="red">函数模板的参数推导机制为什么得以实现？因为我们在函数调用的时候实际上向其提供了类型信息，因此它得以正确的推导类型。</font>

也就是说，对于上面的例子来说，编译器可以通过`iter`和`*iter`来正确的推导`I`和`T`的类型，即使我们想要将`T`类型作为返回值，只要把`void`改成`T`，这段代码仍然是有效的。

但是，如果我们没有提供类型信息呢，考虑这样的例子：

```cpp
template <class T>
T fun() {
    return T();
}
```

那么调用`func()`时，编译器是无法得到你要返回的类型的。除非你使用`func<int>()`这样的显式指定模板类型来调用。

> 在C++中，模板参数推导主要是基于函数的实参来推导模板参数的。当模板参数仅用于函数的返回值时，编译器无法仅通过函数调用来推导出这个参数的具体类型。
>
> 考虑以下例子：
>
> ```cpp
> template <class T>
> T fun() {
>     return T();
> }
> ```
>
> 当你调用`fun()`时，编译器无法知道你想要返回什么类型，因为你没有提供任何关于`T`的信息。你必须显式地指定模板参数，例如`fun<int>()`。
>
> 但在你给出的例子中，`T`是基于`*iter`的类型来推导的，所以当你传递一个迭代器或指针给`fun_2`时，编译器可以通过`*iter`的类型来推导出`T`的类型。
>
> 如果你想要`fun_1`返回一个`T`类型的值，那么确实可以这样做：
>
> ```cpp
> template <class T, class I>
> T fun_1(I iter) {
>     T tmp = 0;
>     std::cout << tmp << std::endl;
>     return tmp;
> }
> ```
>
> 但在这种情况下，返回值的类型并不是基于模板参数推导得出的，而是由你在调用`fun_2`时传入的迭代器或指针来决定的。

那么，为了解决函数模板参数推导不能解决的问题，我们可以考虑使用内嵌类型：

```cpp
template<class T>
struct MyIter{
	typedef T value_type;
	T *ptr;
	...
};
template<class I>
typename I::value_type func(I ite){
	return *ite;
}
...
MyIter<int> ite(new int(8));
cout << func(ite);
```

在这里，`I`的类型首先被推断为`MyIter`，据此我们使用`typename MyIter::value_type`来确定`MyIter`的模板实体类型，在这里实际上就是`int`（`T`和`value_type`都是`int`）。

注意，这里的关键字`typename`是不能省略的，因为在模板实例化之前，编译器无从确定`I`的类型，甚至不能保证它一定有`value_type`成员。即使确定`I`是`class`，也保证它有`value_type`成员，也不能确定它到底是一个类型、成员函数还是一个数据成员。因此必须使用`typename`显式告诉编译器它是一个类型。

但是还是有问题！<font color="red">如果`I`是迭代器，但是真的不是`class`呢？比如它是原生指针，既具有迭代器的属性，又不具备`value_type`这样的类型属性。</font>

`STL`的设计准则之一就是尽量满足泛型性，对于任何类型的输入尽量保持合理的输出。因此我们使用模板偏特化(template partial specialization)来解决这个问题。

模板偏特化的大致意义是：<font color="red">如果一个类模板拥有一个以上的模板类型参数，我们可以针对其中某个或数个（如果是全部则是全特化了）模板类型参数进行特化。也就是说，为其中某一部分模板指定具体类型，然后提供一份实现。</font>

例如，对于这样的一个类模板：

```cpp
template<class T>
class C{...};
/*
其实，class C实际展开是:
class C<T>{
	...
};
*/
```

我们可以提供这样的一份偏特化版本:

```cpp
template<class T>
class C<T*>{ ... };
```

这个偏特化（为什么不是全特化？稍后解释）版本，接受“任何类型的原生指针”作为参数。

> 这是偏特化。原因是它特化了一个模板参数，但仍然保留了一定的泛化性（即对于任何类型T的指针T*）。
>
> 全特化是为模板参数指定了具体的类型，没有任何泛化性。而偏特化则是为模板参数指定了部分具体的类型，但仍然保留了一些泛化性。在这个例子中，`C<T*>`是对任何类型T的指针进行特化，所以它是偏特化。

既然我们可以为"任何类型的原生指针"提供一份特化版本的模板实现，那么自然就可以解决上面提到的问题了。现在，我们可以针对"迭代器为原生指针"的版本进行特化了。

首先，我们定义了一个用于"萃取"迭代器"指向的对象的类型"的类模板:

```cpp
template<class T>
class iterator_traits{
	typedef typename T::value_type value_type;
};
```

乍一看这段代码有点冗长，逐层进行解析:

- `typedef`尝试定义一个别名。
- `typename T::value_type`从`T`类型中取得一个`value_type`属性，并声明其为一个类型。
- `value_type`将作为`T::value_type`的别名。

这段代码意味着，如果`iterator_traits<T>`中的`T`具有自己的`value_type`，那么就将`value_type`作为`T::value_type`的别名。

上面内嵌模型的例子中，`func`的函数声明可以改写为:

```cpp
template<class T>
typename iterator_traits<T>::value_type func(I ite){...}
```

