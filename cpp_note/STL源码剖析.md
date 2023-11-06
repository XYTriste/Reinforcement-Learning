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

这相当于我们给`T`加上了一层封装，这样做有什么意义呢？

意义就在于我们可以针对`iterator_traits`这个类模板进行特化，使其对"任意`T`类型的指针"包含不同的`value_type`类型名:

```cpp
template<class T>
class iterator_traits<T *>{
	typedef T value_type;
};
```

这将使得`value_type`成为"指针所指向的对象"的类型名。

最后还有一个小小的问题是，如若指针类型是"指向常量对象的"指针呢？也就是说，假如`T`的实际类型是`const int *`，上述偏特化的`value_type`将成为一个`const int`，而我们可能不希望去声明一个无法修改的对象。

解决方法也很简单，那就是针对常量指针同样声明一个特化版本:

```cpp
template<class T>
class iterator_traits<const T*>{
	typedef T value_type;
};
```

如此就可以解决几乎所有有关于类型识别的问题了。当然，如果想要使得`traits`萃取能够有效运作，每一个迭代器都需要遵循约定，自行以内嵌类型定义的方式定义出相应类型。

最常用到的迭代器类型有五种：`value_type`、`difference type`、`pointer`、`reference`、`iterator category`。如果希望自定义的容器能够兼容STL，则应该：

```cpp
template<class T>
class iterator_traits{
	typedef typename T::iterator_category iterator_category;
	typedef typename T::value_type value_type;
	typedef typename T::difference_type difference_type;
	typedef typename T::pointer pointer;
	typedef typename T::reference reference;
};
```

注意，<font color="red">`iterator_traits`必须针对传入类型为指针和常量指针的版本进行特化。</font>

#### 3.4.1 迭代器类型: value_type

具体内容已在上一节介绍过。

#### 3.4.2 迭代器类型： difference_type

`difference_type`用来表示两个迭代器之间的距离，因此它可以用来表示一个容器的最大容量。

从我个人理解来说，`difference_type`像是"一单位"的距离，比如对于数组`int sz[]`而言。从空间概念上来看，`sz[2]`和`sz[3]`相差"一`int`"的距离。从字节表示上来看，它们的起始地址一般情况下相差`4`个字节。这里的"一`int`"就是`difference_type`的单位。

也就是说，针对一个连续容器而言，`difference_type`表示了两个迭代器之间的距离，这个距离指的是"单位距离"而不是"字节距离"。

```cpp
template<calss I, class T>
typename iterator_traits<I>::difference_type
count(I first, I last, const T& value){
	typename iterator_traits<T>::difference_type n = 0;
	for(; first != last; first++){
		if(*first == value){
			n++;
		}
	}
	return n;
}
```

假如`I frist`和`I last`表示了某个容器的起始位置和结束位置，那么"一单位"就是`*first`的类型的大小。`difference_type`则是一个有符号的整数，表示该范围内包含了多少个这样的类型的元素。

和`value_type`几乎一样，<font color="red">`difference_type`也需要对指针和常量指针进行特化，方法一样。</font>

#### 3.4.3 迭代器类型: reference_type

C++中，函数如果要返回一个左值，都是以引用方式返回（右值不允许赋值操作，所以不会有`func() = 1`这样的写法）。如果`p`是一个迭代器类型，它指向的对象(`value_type`)为`T`，那么`*p`不应该是`T`类型，而是对`T`类型的引用。同理，如果`p`是一个`const iterator`，那么`*p`不应该是`const T`，而是对`const T`的引用。

#### 3.4.4 迭代器类型: pointer type

如果"传回一个左值，它代表着迭代器`p`指向的对象"(引用)是可以的，那么"传回一个左值，它代表着迭代器`p`所指向的对象的地址"（指针）也一定可以。

因此，对原生指针以及const指针进行特化时，不止需要对指针的特殊情况进行`typedef`，同时也要对引用进行`typedef`。

#### 3.4.5 迭代器类型: iterator_category

首先，我们讨论迭代器的分类。

<font color="red">根据移动特性与实现操作，迭代器被分为五类:</font>

- input iterator: 这种迭代器指向的对象，表示一个"来自其他地方的输入"，因此不可改变，只读。
- output iterator: 只写。
- Forward iterator: 允许"写入型"算法在这种迭代器形成的区间上进行读写操作，从名字也可以看出来它是一个前向迭代器，单向的。
- Bidirectional iterator: 可以双向移动的迭代器，可读写对象。

- Random Access iterator: 功能最强大的迭代器，支持随机读写访问。

从描述的顺序就可以看出，最上方的迭代器受到的限制越多，越到后面实现的迭代器的功能就越强。

上述描述内容涉及到的一个问题是，如果我们要针对不同类型的迭代器设计算法，如何尽可能的提高效率？

例如，一个`input iterator`和一个`Random Access iterator`都支持前向迭代的功能，但是`input iterator`只能进行顺序读，`RAI`则可以进行随机读。如果我们有这样的函数:

```cpp
void advance(Iterator& it, int n){
	while(n--)
		it++;
}
```

这当然对`input iterator`和`Random Access iterator`都有效，但是因为`RAI`是支持随机写的，因此显然对于它而言，这样的代码更有效率:

```cpp
it += n;
```

那么，如何针对不同的迭代器实现不同的前向迭代方式呢？一种方法是进行判断并声明不同的函数：

```cpp
template<class InputIterator, class Distance>
void advance(InputIterator& i, Distance n){
	if(is_random_access_iterator(i)){
		advance_RAI(i, n);
	}else if(...){
		...
	}
	...
}
```

<font color="red">这样做的不好之处在于将负担交给了运行期，因为直到运行时程序才知道`i`的具体类型，才知道具体调用哪个函数。这降低了程序执行的效率。</font>

另一种方式则是使用函数重载，这样在编译器就能够确定具体调用哪个函数。

但是我们也可以看到，上面这个`advance`的两个参数都是模板类型，没有具体的类型。在不提供其他参数的情况下无法重载。因此为了让它成为重载函数，它必须包含一个确定类型的参数。

这就用到了我们的`traits`萃取技术。首先，我们使用五个`class`来代表五种迭代器类型:

```cpp
class input_iterator_tag{ };
class output_iterator_tag{ };
class forward_iterator_tag: public input_iterator_tag{ };
class bidirectional_iterator_tag: public forward_iterator_tag{ };
class random_access_iterator_tag: public bidirectional_iterator_tag{ };
```

现在我们可以进行函数重载了，只要在`advance`函数的重载版本中指定不同的迭代器类型参数并提供不同的实现即可，函数内部并不需要用到这个迭代器类型，该类型只是用来激活不同的重载版本。

现在我们整理一下内容，假设我们需要自定义一个迭代器，并希望它实现`advance`函数的功能，我们应该为其指定一个`iterator_category`:

```cpp
template<class T>
class MyIterator{
	...
	using iterator_category = std::random_access_iterator_tag;
}
```

当我们将自定义的迭代器传递给STL容器（例如vector）时，萃取技术会得到其类型:

```cpp
template<class T>
class iterator_traits{
	...
	typedef typename T::iterator_category iterator_category;
};
// MyIterator::iterator_category 经过萃取后， iterator_category成为了std::random_access_tag的别名。
```

据此，我们假设通过`__advance`函数来调用STL标准库中的对应函数:

```cpp
template<class InputIterator, class Distance>
void advance(InputIterator& i, Distance n){
	__advance(i, n, iterator_traits<InputIterator>:: iterator_category());	
}
```

这样就会根据其实际类型`std::random_access_tag`来调用不同的重载版本了。

> 这段代码更准确地描述了C++中的迭代器萃取技术和如何根据迭代器的类型调用不同的`advance`函数版本。但是，仍有一些需要纠正和澄清的地方：
>
> 1. **自定义迭代器的类别**：在`MyIterator`类中，你已经正确使用了`using`来定义`iterator_category`。这是一个好的实践，因为它清楚地表明了迭代器的类别。
>
> 2. **迭代器特性的萃取**：虽然你展示了如何为一个迭代器定义一个`iterator_traits`类，但实际上，标准库中已经有了`std::iterator_traits`。你不需要重新实现它，除非你正在创建一个与标准库不兼容的自定义迭代器。
>
> 3. **advance函数的实现**：在`advance`函数的实现中，你提到了一个名为`__advance`的函数，这个函数似乎是根据迭代器的类别来调用不同的函数重载。然而，你没有提供`__advance`函数的实现或其重载版本。在实际的STL实现中，`std::advance`是已经根据不同的迭代器类别进行了优化的。
>
> 4. **代码的准确性**：在调用`__advance`函数时，你应该传递一个实际的类别对象而不是一个类型。代码应更正为：
>    ```cpp
>    typename iterator_traits<InputIterator>::iterator_category category;
>    __advance(i, n, category);
>    ```
>    这里，`category`是从迭代器特性中萃取出的迭代器类别的一个实例。
>
> **知识点总结**：
> - **迭代器类别**：迭代器被分为不同的类别，如输入迭代器、前向迭代器、双向迭代器、随机访问迭代器等，每种都有其特定的功能和限制。
> - **萃取技术**：通过使用`iterator_traits`，可以获取关于迭代器的信息，如其类别、值类型、差异类型等。这对于编写可与多种类型的迭代器一起工作的泛型代码非常有用。
> - **函数分派**：根据迭代器的类别，可以调用最适合该迭代器性能特性的函数版本。例如，对于随机访问迭代器，有可能直接跳转到序列中的特定位置，而对于前向迭代器，则可能需要逐个元素地前进。
>
> 这些概念对于理解C++中的迭代器和泛型编程至关重要，它们帮助开发者编写高效、可重用的代码。

注意上面的这行代码:

```cpp
__advance(i, n, iterator_traits<InputIterator>:: iterator_category());	
```

关键在于:

```cpp
iterator_traits<InputIterator>:: iterator_category()
```

这实际上调用的是:

```cpp
std::random_access_iterator_tag()
```

这创建了一个临时对象作为参数传递给函数，函数据此判断调用哪个重载版本。

书中P96给出了`SGI STL`中的真正实现，区别仅在于定义了一个内联函数:

```cpp
template<class InputIterator>
inline typename iterator_traits<InputIterator>::iterator_category iterator_category(InputIterator& i){
	typedef typename iterator_traits<InputIterator>::iterator_category category;
	return category();
}
```

其实功能是完全一样的，都是传递一个临时对象来调用不同重载版本，只不过单独定义一个函数的方式可能有助于减少函数参数中写的太长太复杂，这样的写法也便于后面修改。

<font color="red">任何一个迭代器，它的真实类型永远它所能具有的功能中最强的那个。</font>这句话其实很好理解，一个`Random access iterator`一定是一个`Forwarditerator`，反之则不然。

<font color="green">还有一个小技巧：在上述代码中模板名命名为`Inputiterator`，这是一个STL的命名规则："以算法可以接受的最低阶的迭代器类型为其模板类型参数命名。"</font>

还有一个值得一提的一点就是，在刚才的"五种迭代器类型"的部分，我们描述了一些继承关系。

为什么要这么做？书中P97给了比较详细的解释，这里简要说明。

还是假设我们要实现`advance`函数，对于`InputIterator`和`ForwardIterator`，它们在该函数下的实现并不任何不同（因为它们都是顺序前向迭代）。因此按理来说，我们只需要编写`InputIterator`的`advance`函数实现即可，在`ForwardIterator`的`advance`函数实现中只需要对`InputIterator`的`advance`函数进行转调用即可。

但是，我们可以消除这样的转调用，从而减少代码的冗余。方法就是实现刚才所提到的继承关系。

这也和重载函数的机制有关，当我们编写了一个重载函数调用的时候，编译器会为其找到"最匹配的版本"。如果没有类型完全一致的版本，则会找到"差不多的版本"。

也就是说，如果我们使用`InputIterator i`调用`advance`函数，类似这样:

```cpp
advance(i, n, input_iterator_tag);
```

如果使用的是`ForwardIterator i`，调用只有标记类型的参数不同:

```cpp
advance(i, n, forward_iterator_tag);
```

但是我们说过了，二者的`advance`操作完全一样，因此通常情况下在`ForwardIterator`特化版本的`advance`版本内部会这样调用:

```cpp
advance(i, n, input_iterator_tag);
```

这将导致转调用，但是有了继承关系，即使我们调用`advance(i, n, forward_iterator_tag);`，即便我们没有设计`ForwardIterator`的`advance`版本，也会转调用`InputIterator`的`advance`版本。

### 3.5 std::iterator的保证

为了符合规范，任何迭代器都应该提供相应的五个迭代器的类型，以利于`traits`的萃取。STL中提供了一个标准`std::iterator`（书上P100），用户自定义的迭代器只要继承自它，就可以保证符合STL的规范。

### 3.6 iterator完整代码

书中P101，这部分代码可以好好看看。

### 3.7 __type_traits

望文生义，`iterator_traits`用来萃取`iterator`(迭代器)的`traits`(特征)。那么`__type_traits`自然而然就是萃取`type`(类型)的`traits`(特征)。

这里指导的类型特征是指：该类型的对象是否具有平凡的默认构造函数、拷贝构造函数、拷贝赋值运算符、析构函数等。如果一个类型具备这些特征，我们对这个类型进行这些操作的时候就可以采取较为有效的方式（例如，不去调用它的默认构造函数）。

根据规范，在程序中我们通常用这样的方式来运用`__type_traits<T>`:

```cpp
__type_traits<T>::has_trivial_default_constructor
__type_traits<T>::has_trivial_copy_constructor
__type_traits<T>::has_trivial_assignment_operator
__type_traits<T>::has_trivial_default_destructor
__type_traits<T>::is_POD_type	//POD: plain old data
```

我们希望萃取出来的结果仍然是一个类型，而不是一个布尔值。这与上面函数重载减少转调用的原理相同，我们可以通过结果的类型进行参数推导进而实现函数重载调用。具体来说，结果将会是:

```cpp
class __true_type{};
class __false_type{};
```

这样的空类不会带来额外负担，但是又能够标识它是否具有相应的属性，满足我们的要求。

默认情况下，`__type_traits`的模板类中会将这五个属性都别名为`__false_type`，因为这是更保守的做法。

究竟什么时候一个类才应该有自己的非平凡构造函数等函数呢？一个准则是:

<font color="red">如果一个类含有指针成员，并对它进行内存配置，那么这个类就需要实现出自己的非平凡函数。</font>

## 4. 序列式容器

### 4.1 容器的概念和分类

#### 4.1.1序列式容器

所谓的序列式容器，指的是元素从内存分布上来说有序，但元素值本身未必有顺序。C++本身提供一个序列式容器`array`，STL另外提供了`vector`、`list`、`deque`、`stack`、`queue`、`priority-queue`等序列式容器。

### 4.2 vector

#### 4.2.1 vector概述

相较于C++本身提供的`array`，`vector`在功能上与其非常相似。它们唯一区别在于空间运用的灵活性。`array`是静态空间，分配后只能保存固定数量的元素，如果想要插入更多的元素，只能通过新分配更大的空间，再将旧空间中的数据拷贝到新空间中去。

`vector`则是动态空间，随着元素加入自行扩充空间来容纳新的元素。

#### 4.2.2 vector定义摘要

这部分给出了vector的部分源代码，没有太多值得商榷的内容。

大致分为嵌套类型定义（用于`iterator traits `）以及实现内存管理的`allocator`，再加上3个指针（或者说迭代器，分别表示`vector`的起点，当前终点，以及可用内存的终点）。

其他函数都依靠这几个指针进行具体实现。

具体代码在书上P116。

#### 4.2.3 vector的迭代器

`vector`维护的是一个连续线性空间，所以不论其元素类型是什么，普通指针都可以作为vector的迭代器，并满足所有迭代器的操作。(从书中P116的代码也可以看出vector的迭代器实际上就是普通指针)。

因此，<font color="red">vector提供的是`Random access iterator`。</font>

#### 4.2.4 vector的数据结构

vector简单的采用线性连续空间，`iterator start`、`iterator end_of_storage`、`iterator finish`分别表示目前使用空间的起点，目前可用空间的结尾以及目前使用空间的终点。

为了降低空间配置的成本，vector的实际容量会比客户端需求量大一些。换句话说，一个vector的容量永远大于等于其存储的元素数量大小。

<font color="red">如果在满载时继续向vector插入元素，则容量会扩充到原来的两倍。如果两倍容量仍然不足，就继续扩充至足够大的容量。</font>

另外记住的一点是，当满载并继续插入时，`vector`不得不向内存分配器请求一块更大的内存并将元素复制过去。因此实际上经历了"重新分配、元素移动、释放原空间"的过程。

#### 4.2.5 vector的构造与内存管理:constructor, push_back

这部分给出了具体实现，代码在P120。

没有太多值得额外提的内容，不同的`constructor`会根据参数的不同选用不同的配置方式。`push_back`则会检查是否还有可用空间，如果有可用空间则在可用空间上构造，否则申请空间并重新配置、移动数据、释放原空间。

#### 4.2.6 vector的元素操作: pop_back，erase，clear，insert

`pop_back`没有什么特色，无非是将`finish`迭代器回退一个元素，并通过`destroy`函数销毁该元素。

`erase`提供了两个重载版本。第一个版本将迭代器范围`[first,last)`范围内的元素擦除。具体来说：

首先调用`copy`函数将`[last, finish)`范围内的元素复制到以`first`为起点的地址上，copy函数会返回一个指向复制完成后最后一个元素所在位置之后的迭代器`target`。即:`target = first + (last - first)`。

随后，销毁`[target, finish]`范围内的元素，`erase`需要擦除的元素已经被覆盖。

最后，调整`finish`迭代器指向的位置。



第二个版本指定擦除某个位置的元素，同样是通过覆盖擦除对应位置元素。只不过只需要销毁最后一个元素并调整`finish`即可。



P125页给出了insert函数的实现。

首先，判断备用空间的大小是否足够容纳新增的元素。

如果足够，计算从插入点到结尾包含多少个元素，这些元素需要进行后移。

<font color="red">如果插入点到结尾的元素数量大于新增的元素数量，</font>那么首先计算出有多少个元素要被挤到原来的`finish`后面去(其实就是`[finish - n, finish)`范围内的元素被移到后面去)。然后，将这部分的元素拷贝到以`finish`为起点的备用空间中去。然后，将插入点`position`到`finish-n`（也就是那些会被往后挤，但不会超出原来的`finish`）的元素使用逆向复制`copy_backward`的方式复制到以原来的`finish`为结尾的空间中去。最后，调用`fill`填充`[position, position + n)`即可。（不要忘了更新`finish`）。

```cpp
//假设vector此时包含元素: 1 2 3 4 5
//现在要插入2个元素0，插入点在元素2之后
unitialized_copy(finish - n, finish, finish);
//这行代码将元素4 5复制到finish为起点的空间中，此时vector元素为1 2 3 4 5 4 5
copy_backward(position, old_finish - n, old_finish);
//这行代码将元素3复制到以5(第一个5)为终点的空间中，此时vector元素为1 2 3 4 3 4 5
fill(position, position + n, 0);
//这行代码将元素0填充到以3为起点的空间中，此时vector元素为1 2 0 0 3 4 5
finish += 2		// 不要忘了更新finish
```

<font color="red">反之，如果插入点之后的现有元素个数"小于等于"新增元素的个数。</font>这意味着插入点之后的元素都要被挤到`finish`的后面去，甚至并不一定直接在`finish`作为起点的位置。也就是说，假如`vector`中原先有5个元素，现在在第二个元素之后插入6个元素，那么原`vector`插入点之后的3个元素会被挤到原`finish`（第五个位置）后的`5+6-3-5 `个位置去，也就是第`8`个位置。

虽然说的很绕口，但是想象一下就很好理解。

那么，首先我们需要为新加入的元素中"超出原`finish`的部分（也就是说它比插入点之后现有元素的个数多多少）"进行填充。填充完成后，`finish`被更新为`finish + 超出部分的个数`。新的`finish`同样是"原插入点后面的元素被挤到的起始位置"。因此以`uninitialized_copy(position, old_finish, finish)`的方式就可以将原来插入点之后的元素拷贝到新的位置。接着，我们将`finish`加上插入点之后的元素个数，这样`finish`就到达了真实插入元素后的结尾。接着，我们调用`fill(position, old_finish, x_copy)`即可完成插入。

---

以上是备用空间大小充足的情况，现在讨论备用空间不足的情况。

当备用空间不足时，显然我们就需要为vector重新分配空间。新的空间大小为:

```cpp
const size_type old_size = size();
const size_type len = old_size + max(old_size, n);
```

显然，如果扩容到原先的两倍足以容纳新的元素，那么就会扩容至原来的两倍。否则就会扩容至`old_size + n`的大小。

接下来的过程就简单了，首先向分配器要求得到`len`个大小的内存。然后将插入点之前的元素拷贝到新的空间中，随后对插入点后的`n`个元素进行填充，最后将插入点之后的元素拷贝到填充完之后的内存中。

当然，根据第二章内存分配器中的知识，如果在分配内存或者填充空间的过程中发生了异常，则应该遵循`commit or rollback`原则，对分配的内存以及填充的部分值进行回滚，销毁新分配的空间。

即使上述一切正常，最后也不要忘记了手动销毁(实际上是把这部分内存归还给`allocator`)原先`vector`使用的内存。

### 4.3 list

#### 4.3.1 list概述

list的好处在于，它每次插入或删除一个元素，就配置或释放一个元素的内存空间。因此它对于空间运用有着绝对的精准。

而且，对于任何位置元素的插入或删除，它永远是常数时间。

相较于vector，取用哪一个容器更好？这取决于元素的多少，元素的构造复杂度（是否有平凡的构造函数）等。

#### 4.3.2 list的节点

list的节点很好理解，它是一个双向链表。

#### 4.3.3 list的迭代器

正如前面对vector的描述，vector使用的是一段连续的内存空间。因此可以使用原生指针作为迭代器，并使用`++`、`--`、`+=`等运算符来实现随机读。但是list作为双向链表，直接对原生指针使用这些操作显然不可行。

那么，list的迭代器应该做到什么？就像我们对双向链表的访问一样，双向链表支持向前和向后遍历（说明不只是`Forward`），假设我们在第3个节点，想要访问第7个节点，就只能通过`next`指针一个一个的迭代过去（说明不支持随机读）。那么，显然list应该使用`Bidirectional iterator`。

书中代码在P130，这里简单介绍大概list迭代器的设计。

首先，上来就是一个令人惊讶的点，list迭代器的模板声明居然包含了3个参数（人家vector才一个），分别是`T`、`Ref`和`Ptr`。

这里我需要详细的描述思路，以免之后自己忘了。

最初我很惊讶的是，从名称来看Ref和Ptr无非代表引用和指针，为什么要为其定义单独的模板参数？而不是直接在类内使用`T &`和`T *`。

随后，在list迭代器的最前方有这样的定义:

```cpp
typedef __list_iterator<T, T&, T*> iterator;
typedef __list_iterator<T, Ref, Ptr> self;
```

这里我非常迷惑，为什么要定义这样的别名？将`T`类型和它的引用及指针作为模板实参的别名为迭代器，而使用了模板参数`T`、`Ref`、`Ptr`的定义为`self`。

随后还有这样的定义:

```cpp
typedef T value_type;
typedef Ptr pointer;
typedef Ref reference;
```

根据查阅网上的说法，这样做是为了"保证我们使用常量迭代器时，不会意外修改迭代器指向的对象值"。

为什么会意外修改？list迭代器设计中包含了`operator *()`函数的重写:

```cpp
reference operator*() const{
	return (*node).data;
}
```

如果没有模板参数`Ref`和`Ptr`，假设我们有这样的调用:

```cpp
const list<int> lst = {1, 2, 3};
list<int>::__list_iterator it = lst.begin();
*it = 2;
```

实际调用的就是:

```cpp
int& operator*() const{
	return (*node).data;
}
```

这就产生了问题，我们意外的修改了一个const list的元素值，这当然是不被允许的，代码应该无法通过编译。

因此，如果我们具有`Ref`和`Ptr`，在list类的设计中可以这样做：

```cpp
template<class T>
class list{
	public:
		...
		typedef __list_iterator<T, T&, T*> iterator;
        typedef __list_iterator<T, const T&, const T*> const_iterator;
    	...
}
```

这样，在实际创建list迭代器对象时，我们就可以根据需要创建对应的迭代器，并阻止意外的修改迭代器指向的对象值。

> 你补充的描述解释得很好，它清楚地指出了`Ref`和`Ptr`模板参数在设计中的重要性，特别是在处理常量和非常量迭代器时保持类型安全性。但是，还有几个小点需要纠正或澄清：
>
> 1. **迭代器的使用**：在你的示例中，你尝试从一个`const list`创建一个非常量迭代器，这在C++中是不允许的。如果`lst`是一个常量对象，你只能从中获取常量迭代器。因此，正确的调用应该是：
>
> ```cpp
> const list<int> lst = {1, 2, 3};
> auto it = lst.cbegin(); // 或 list<int>::const_iterator it = lst.begin();
> ```
>
> 2. **编译错误的解释**：你正确指出，如果尝试通过常量迭代器修改值，代码应该无法通过编译。这是因为常量迭代器的`operator*`返回一个`const T&`，不能被赋值。
>
> 3. **模板别名的定义**：在`list`类的定义中，你展示了如何定义`iterator`和`const_iterator`。这部分是正确的，但是为了避免混淆，应该注意`__list_iterator`很可能是内部使用的，不应该直接在你的类定义外部使用。通常，你会在类内部看到类似以下的定义：
>
> ```cpp
> template<class T>
> class list {
> public:
>     // ...
>     typedef __list_iterator<T, T&, T*> iterator;
>     typedef __list_iterator<T, const T&, const T*> const_iterator;
>     // ...
> };
> ```
>
> 这里，`__list_iterator`是一个假设的内部实现细节，实际的标准库实现可能会有所不同。
>
> 4. **清晰的结论**：最后，在你的结论中，你提到了使用`Ref`和`Ptr`可以创建适当类型的迭代器，并防止意外修改。这是一个很好的总结，因为它强调了这种设计的目的是为了类型安全，特别是在常量和非常量上下文中。
>
> 总的来说，你的解释是对的，只需要对上述几点进行微调和澄清。

解释完了这个令人疑惑的问题，别的部分就很清晰了。无非就是实现迭代器的前后迭代(通过`prev`和`next`指针)以及取值。

#### 4.3.4 list的数据结构

list不仅是一个双向链表，而且是一个环状双向链表（首尾相连），所以只需要一个指针就可以完整表示整个链表。

为了符合STL规范中对于区间"前闭后开"的要求，通常会在链表的尾部添加一个空白节点表示`end()`。每次添加新节点时，只要让新节点的`next`指向`begin().prev`，新节点的`prev`指向`begin().prev.prev`，再让`newnode.prev.next = newnode`，最后让空节点的`prev`指向新节点即可。

> 这部分GPT4.0的解释更加完美：
>
> 你的描述对于`list`作为环状双向链表的特性是正确的，但是有一些描述上的不精确之处和可能引起混淆的地方。以下是一些建议和修正：
>
> 1. **环状双向链表的描述**：确实，`list`是一个环状双向链表，但这种设计主要是为了简化迭代器的实现和管理，而不仅仅是为了用一个指针表示整个链表。
>
> 2. **空白节点的描述**：你提到了在链表尾部添加一个空白节点来表示`end()`，这是正确的。但这个节点通常被称为"哨兵节点"或"哑节点"，它的存在确实是为了满足STL的"前闭后开"区间规范。
>
> 3. **节点添加的描述**：你描述的节点添加过程有些混淆。考虑到`list`是一个环状双向链表，通常的插入过程是这样的：
>
>    - 新节点的`next`指向哨兵节点。
>    - 新节点的`prev`指向哨兵节点的`prev`（即原来的最后一个节点）。
>    - 原来的最后一个节点的`next`指向新节点。
>    - 哨兵节点的`prev`指向新节点。
>
>    这样，新节点就被正确地插入到链表的尾部。
>
> 4. **清晰性**：为了清晰地描述这个过程，可以考虑使用伪代码或更详细的步骤描述。
>
> 修正后的描述可能是这样的：
>
> ```plaintext
> list不仅是一个双向链表，而且是一个环状双向链表，这种设计主要是为了简化迭代器的实现和管理。为了符合STL规范中对于区间"前闭后开"的要求，通常会在链表的尾部添加一个哨兵节点（或称为哑节点）来表示`end()`。每次添加新节点时，新节点的`next`指向哨兵节点，新节点的`prev`指向哨兵节点的`prev`，然后原来的最后一个节点的`next`指向新节点，最后哨兵节点的`prev`指向新节点。
> ```
>
> 这样的描述更加清晰和准确。

#### 4.3.5 list的构造与内存管理

`list`默认使用`alloc`作为空间配置器，并据此另外定义了一个`list_node_allocatro`，以节点为单位配置内存。

当我们以`push_back`向`list`插入节点时，实际内部调用的是`insert(end(), node)`这样的形式。

<font color="red">而当我们调用`insert()`函数向`list`中插入元素时，新的元素将处于插入点的前方。例如，在`0 1 2 3 4`中以元素`2`作为插入点时，插入元素后为`0 1 X 2 3 4`，这也是STL针对插入操作的标准规范。</font>

> 其实这个插入规范并不难理解，就好像一个队伍中我站在了某个人的位置上。那么这个人自然就到我的后面去了。换句话说，我(新的元素)就处于他（插入点）的前方了。

#### 4.3.6 list的元素操作

`list`提供了挺多对于元素的操作，下面逐个进行讲解：

`push_front`，内部其实调用了`insert(begin(), node)`。

`push_back`，内部其实调用了`insert(end(), node)`。

`erase`，由于`list`实际上是双向环状链表，每一个节点都包含了指向了前驱和后继节点的指针。因此只要让它的前驱节点的`next`指针和后继节点的`prev`指针更新即可将节点从链表中删除。然后让内存配置器回收内存即可。

`pop_front`，内部实际调用了`erase(begin())`。

`pop_back`，内部实际调用了`erase(--end())`。

`clear`，清除所有节点（整个链表），首先从空节点的`next`指针指向的节点（`begin()`）出发。循环清除每个节点，最后将空节点的`next`和`prev`指针都指向自己。

`remove`，从链表中删除值为`val`的节点。循环整个链表，找到对应节点后调用`erase`。

`unique`，从链表中删除**连续且值相同**的元素，同样是循环整个链表，使用双指针分别指向当前节点和下一个节点。如果二者的值相等，则将下一个节点的值删除，并将指向下一个节点的迭代器更新为指向当前节点。然后再使用`++`的方式使其指向下一个节点。继续比较。如果二者的值不相等，就将指向当前节点的迭代器更新为指向下一个节点。

`transfer`，将一段范围内的节点迁移到`position`之前。假设一段范围是`[first, last)`，那么实际上就是要更新这些指针：

- `first`节点的`prev`指针
- `first.prev`节点的`next`指针
- `last`节点的`next`指针
- `last.next`节点的`prev`指针
- `position`节点的`prev`指针
- `position.prev`节点的`next`指针

<font color="red">注意，`transfer`并不是一个公开接口。`list`公开提供的是接合操作`splice`。将某连续范围内的元素从一个`list`移动到另一个。</font>

为了提供接口灵活性，`splice`具有多个重载版本。包括将另一个`list`接合到`position`之前，将某个元素接合到`position`之前，或将某个范围内的元素接合到`position`之前。

`merge`，将调用链表和参数链表进行合并，合并时的内容需要经过递增排序。内部调用`transfer`的接合某个元素的版本来实现。

`reverse`，反转整个链表。内部其实就是循环调用`transfer`将元素接合到`begin()`之前。

`sort`，由于list的迭代器并不是`Random Access Iterator`，因此无法直接使用STL的`sort`，而是自己内部实现了一个成员函数`sort`。

### 4.4 deque

#### 4.4.1 deque概述

类似但不同于`vector`，`deque`是双端队列，它是一种双向开口的连续线性空间。

虽然`vector`理论上可以调用`insert(begin(), val)`的方式在头部插入值实现`deque`，但是每次都要将元素后移显然效率太低。而deque则允许以常数时间在头端进行元素的插入删除操作。

另一个差异在于，deque没有容量的概念，vector中插入元素而容量不足时就会发生内存分配以及数据迁移。而deque动态的以分段连续空间组合而成，随时可以新增一段空间链接起来。

deque虽然提供`Random Access Iterator`，但是复杂度比`vector`高太多。

#### 4.4.2 deque的中控器

正如上面所说，deque实际上是以分段的连续空间组合而成。如果在deque的前端或者尾端插入元素而连续空间中没有足够位置时，则会配置一段新的连续空间，串接在deque的前端或尾部，造成连续的假象。

deque采用一块`map`（我个人觉得其实就是一个数组）来作为中控，这个`map`很小，每一个节点都是一个指针，指向一块较大的缓冲区区域（就是分配给deque的空间）。与vector模板不同的是，除了指定存储数据的类型和使用的内存配置器，deque模板还可以指定缓冲区大小（默认情况下为`512bytes`）。

#### 4.4.3 deque的迭代器

deque是分段的连续空间，因此其迭代器不仅要在连续空间内迭代。还要考虑边界问题（如果当前迭代器指向的节点为当前连续空间内最后一个节点，现在执行`++`操作应该怎么办？）。

因此，为了能够正确的完成`RAI`所要做的事，deque的迭代器必须要学会如何在不同的连续空间内跳转，这就要求它随时掌控整个map。

书中迭代器实现代码在P146，这里给出简单解释。

一如往常的包含了一些常规的迭代器定义，包括迭代器类型等。稍有不同的是迭代器内部定义了四个指针，分别是`cur`、`first`、`last`、`node`，它们分别表示：

- `cur`:指向缓冲区中某个元素，即代表迭代器指向的元素。
- `first`:当前所处的缓冲区（连续空间）的头
- `last`:当前所处的缓冲区(连续空间)的尾
- `node`:指向中控map的指针

此外，迭代器实现类中还包含了一个静态函数`buffer_size`，用来计算每个缓冲区应该包含多少个元素。

```cpp
inline size_t __deque_buf_size(size_t n, size_t sz){
	return n != 0 ? n : (sz < 512 ? size_t(512 / sz) : size_t(1));
}
```

> 这个函数名为`__deque_buf_size`，它接受两个参数：`n`和`sz`。函数的目的是计算deque的缓冲区大小。
>
> 1. 如果`n`不为0，函数直接返回`n`。
> 2. 如果`n`为0，函数会检查`sz`是否小于512。
>    - 如果`sz`小于512，函数返回`512 / sz`的结果。
>    - 否则，函数返回1。
>
> 简而言之，这个函数是为了确定deque的缓冲区大小，确保其至少能容纳一个元素。如果每个元素的大小小于512字节，那么缓冲区可以容纳多个元素，以使整个缓冲区的大小至少为512字节。如果元素的大小大于或等于512字节，缓冲区只能容纳一个元素。

deque迭代器包含了一些关键性的行为，例如`++`、`--`、`+=`等等。由于涉及到了跳转缓冲区的操作，因此实现比较复杂，书中代码在P148，这里给出简单解释。

首先，迭代器中定义了一个`set_node`函数，这个函数接受map中的一个节点作为参数，将当前迭代器所处的缓冲区更新为参数中的缓冲区。同时不要忘记设置`first`和`last`指针，`first`指针很好理解，它就是参数指针指向的缓冲区，而`last`指针则可以由`first + difference_type(buffer_size())`计算而得，这个表达式在指针`first`的地址上加上`*first的类型占用的字节数 * buffersize()`个字节的地址，从而得到缓冲区的尾部。

`operator*`，这个很简单，只要返回`*cur`就可以得到迭代器指向的值了。

`operator->`，同样很简单，只要返回`&(operator*())`即可。

`operator-`，这个比较复杂，代码如下:

```cpp
difference_type operator-(const self& x) const{
	return difference_type(buffer_size()) * (node - x.node - 1) + (cur - first) + (x.last - x.cur);
}
```

> 这段代码是C++ STL中deque容器的迭代器实现的一部分，具体是实现了迭代器之间的减法操作。这个函数的主要作用是计算两个迭代器之间的距离。
>
> 这段代码的主要逻辑如下：
>
> 1. `buffer_size()`：这个函数返回的是每个缓冲区的大小，也就是每个节点可以存储的元素数量。
>
> 2. `(node - x.node - 1)`：这个表达式计算的是两个迭代器所在节点之间的节点数量。<font color="red">注意这里减去1，是因为计算的是两个节点之间的节点数量，而不包括这两个节点本身。</font>
>
> 3. `difference_type(buffer_size()) * (node - x.node - 1)`：这个表达式计算的是两个迭代器所在节点之间的元素数量。每个节点可以存储`buffer_size()`个元素，所以节点之间的元素数量就是节点数量乘以每个节点的元素数量。
>
> 4. `(cur - first)`：这个表达式计算的是当前迭代器所在节点中，当前迭代器位置到节点开始位置的元素数量。
>
> 5. `(x.last - x.cur)`：这个表达式计算的是参数迭代器所在节点中，节点结束位置到参数迭代器位置的元素数量。
>
> 所以，整个函数计算的是两个迭代器之间的元素数量，也就是两个迭代器之间的距离。

纵观代码可以分成两部分：

第一部分`difference_type(buffer_size()) * (node - x.node - 1)`计算两个节点之间越过了多少个缓冲区。注意这里计算使用的是`node`，`node`是`map`中的节点（这也解释了为什么`map`是一段连续空间，如果不是连续空间当然无法计算）。

第二部分就是计算`cur`距离起始点和`x.cur`距离结束点的距离了。

`operator++`，大部分还是常规操作，对`cur`进行`++cur`即可，只是需要额外判断边界问题，如果已经到达当前缓冲区的结尾，则需要调用`set_node(node + 1)`切换缓冲区，同时将`cur`指向`first`。

`operator++(int)`，后置的`++`返回的还是`*this`，只不过内部调用`++(*this)`让前置处理`++`操作。

`operator--`和`operator--(int)`和`++`同理，不赘述。

`operator+=`，这个也比较好理解，首先判断迭代器`+=`后是否还在同一个缓冲区内，是的话直接`cur += n`即可，否则的话就计算一下跳转了几个缓冲区，然后`set_node`切换缓冲区，再继续`+=`即可。

`operator+`，内部调用`operator+=`。

`operator-=`，内部调用`operator+=`，只要将参数置为负值即可。

`operator-`，内部调用`operator-=`。

`operator[]`，内部调用`operator*`和`operator+`，实际上就是`*(*this + n)`。

`operator==`,`operator!=`都是正常比较`cur`指针。

`operator<`，这个首先比较缓冲区的先后顺序，缓冲区一致再比较对应的节点所在的地址大小。

#### 4.4.4 deque的数据结构

书中代码在P150，这里简单说一下。

还是老规矩，定义一些类型别名以供萃取，定义起始节点迭代器和结束节点迭代器来指向当前deque中的起始和结束指针，定义了一个指向map的指针以及定义一个`size_t`类型的`map_size`存储map内包含多少指针。

有了这些东西以后，就可以实现一些常规操作了，利用迭代器即可。

#### 4.4.5 deque的构造与内存管理

这部分书中代码在P152，简单说一下。

deque提供了包含两个参数的构造函数，第一个参数指定初始化时填充在deque中的元素数量，第二个参数则是指定填充值。该构造函数内部调用`fill_initialize(n, value)`来进行填充，而这个函数的内部又调用`create_map_nodes(n)`来为map分配节点，然后在对应的节点上调用`uninitialized_fill`填充。注意，由于填充的数量并不一定整除缓冲区的大小，所以需要将最后一个节点单独进行填充。



这里的重点还是`create_map_nodes`的实现。该函数首先计算填充所需要的节点数，分配的节点个数 = 填充需要的节点数 + 1。

<font color="red">但是，这只是初始化填充操作时所需要的节点数，并不是map管理节点的个数。</font>map管理的节点个数还要在此基础上+2，以保证deque至少可以向前或者向后插入一个缓冲区大小的数据。

每个缓冲区的大小默认为8个元素，用户也可以通过模板参数的方式指定缓冲区的大小。

现在map得到了一些连续的节点指向各自的缓冲区，但是它并不是直接从第一个缓冲区开始填充元素。试想，如果要在deque的前端插入元素，直接从第一个缓冲区开始填充的话就没法在前面插入数据了。

因此，代码中通过`nstart = map + (map_size - num_nodes) / 2`以及`nfinish = nstart + num_nodes - 1`计算出填充数据的起始节点和结束节点，使其前后留出相同个数的节点以供后续的两端插入。

 最后，我们将deque内的`start`迭代器和`finish`迭代器调用`set_node`方法设置对应的节点，并正确的调整它们的`cur`指针即可。



假如我们调用`push_back`在deque的尾端插入值，当已分配的最后的缓冲区中备用空间有两个及以上的空间时，则会正常的插入元素。如果备用空间中只有一个元素时，则会根据情况选择配置一个新的节点作为缓冲区或者更换整个map。

对于`push_front`，和`push_back`是一模一样的道理。唯一一点值得一提的是，由于是前端插入，所以如果配置了一个新的缓冲区，那么迭代器`x`的`cur`指针会指向`x.cur = new_node.last`。每次插入时，都会将`x.cur--`。

那么，什么情况下需要更换整个map呢？答案是显而易见的，如果在执行`push_back`时，缓冲区的备用空间只有一个元素大小，map又没有可用的节点用于在尾端分配新的缓冲区时，就只能更换整个map了。对于`push_front`也是同样的道理。

更换map的实际操作由`reallocate_map()`进行，代码在书中P161，这里给出简单解释。

默认情况下，重新分配的map包含的节点数量为原来使用的节点数量`old_num_nodes`加上`nodes_to_add`（函数参数，默认为1）。

由于触发`reallocate`的条件并不一定是整个map节点都用尽（比如一直进行`push_back`，那么只是尾端的缓冲区用尽了而已），因此函数中进行判断：

- 如果`map_size`大于新需要的节点数量的2倍，这说明原来的map并不是不够用，而是插入的数据都在一边导致"数据放置不平衡"了。因此重新计算一个新的起始节点，新起始节点的前后同样保持相同数量的可用节点。然后把数据重新复制一遍，这样就相当于没有发生内存分配，只是把数据位置平衡一下。
- 如果`map_size`没有大于新需要的节点数量的2倍，那么说明map确实空间不太够用了。新分配一个空间给map，然后将原来的map中节点的数据拷贝过来，最后释放原map。

最后，不要忘记重新设置deque的`start`和`finish`迭代器。

#### 4.4.6 deque的元素操作

`push`操作基本之前都说过了，这里主要谈一下`pop`，代码在书中P163。

其实也没有什么复杂的，`pop_back`无非就是删除`finish.cur`指向的数据，只不过多了一个判断，如果删除后当前迭代器所在的缓冲区为空的话，那么就把缓冲区也释放掉。

`pop_front`也是同理。

`clear`函数，会将deque中的所有元素全部清除，但保留一个缓冲区。执行clear时，首先将除了`start`和`finish`所在的节点之外中间的其他节点（它们一定是满的）中的所有元素析构，并释放这些缓冲区的内存。最后，再将`start.last`到`start.cur`范围和`finish.start`到`finish.cur`范围内的元素全部析构。释放`finish`所在的节点的内存，但是保留`start`的。如果`start`和`finish`指向同一个节点，则不会释放内存。

> 在许多数据结构的实现中，当清除所有元素时，通常会保留一些内存空间，这是为了优化性能。这种做法的主要原因是，如果在清除所有元素后立即有新元素添加，那么保留的内存空间可以立即用于存储新元素，而无需再次进行内存分配。
>
> 对于deque来说，当调用clear函数时，虽然所有元素都被清除，但是保留一个缓冲区可以使得在添加新元素时，不需要立即进行内存分配，从而提高性能。这是一种空间换时间的策略，通过牺牲一些内存空间来提高运行效率。
>
> 此外，由于deque是双端队列，可以在头部和尾部进行插入和删除操作，因此保留一个缓冲区可以同时支持头部和尾部的插入操作，提高了deque的灵活性。

`erase`函数包含了两个重载版本：

- 第一个版本是擦除某个元素，实际上是调用`copy`函数来覆盖被擦除的元素。为了提升效率，如果从`start`到擦除点的元素数量较少，则将前面的元素进行拷贝并覆盖被擦除的元素，最后调用`pop_front`。否则将后面的元素进行拷贝并覆盖被擦除的元素，最后调用`pop_back`。
- 第二个版本则是清除`[first, last)`区间上的元素，如果该区间和`[start, finish)`相同，直接调用`clear()`即可。否则，还是首先判断清除区间前后的元素个数，如果区间前面的元素数量较少，则调用`copy`函数覆盖清除的区间（区间前面的元素数量如果不够可能只覆盖一部分，不过没关系）。然后释放多余的缓冲区并设置新的`start`即可。反之，如果清除区间后面的元素较少，则执行类似的操作，最后设置新的`finish`即可。

`insert`函数，如果插入点在最前方或者最后方，直接调用`push_front`或者`push_back`即可。否则，假设要在前面插入数据，那么计算插入点前面的元素数量和插入点后面的元素数量，假如插入点前面的元素数量较少，则调用`push_front(front())`在deque的最前端插入一个元素，再调用`copy`函数将原来最前端（现在是第二个元素）到插入点的位置的元素向前复制。

这样就会在插入点的前面多出一个元素，将它的值更新为要插入的值即可。

其他条件下做的事情都差不多，都是根据元素数量谁少谁来。

### 4.5 stack

#### 4.5.1 stack概述

先进后出，不允许遍历，顶端存取，都很熟悉了没啥额外值得记的。

#### 4.5.2 stack的完整定义

如果我们已经既有某种容器，将其接口改变后使之符合"先进后出"的特性，形成一个stack，这是可行的。比如`vector`就可以作为一个`stack`的承载容器，只要我们不暴露它的`insert`等`stack`不需要的接口即可。

STL中以`deque`作为默认情况下`stack`的底部结构。又因此，`stack`本身算不上是一个容器，而是一种<font color="blue">适配器</font>。适配器的定义为：<font color="red">修改某物的接口，使其呈现另一种状况。</font>

#### 4.5.3 stack没有迭代器

stack只支持对顶端的元素进行读写等操作，因此不支持任何形式的随机访问。也不提供迭代器。

#### 4.5.4 以list作为stack的底层容器

书中代码在P168，展示了可以以`list`作为`stack`的底层容器，没有什么特色，在此不做解释。

### 4.6 queue

#### 4.6.1 queue概述

先进先出型数据结构，queue支持新增元素、移除元素、从底端（队尾）加入元素、从顶端（队头）取得元素。它不允许遍历行为。

#### 4.6.2 queue完整定义

如同`stack`一般，`queue`需要的功能都由其他容器实现了，没有任何扩展。因此`queue`也可以作为一种容器适配器，底层使用其他容器进行实现。

如果以`deque`作为底层的数据结构，只需要关闭`push_front`以及`pop_back`即可实现`queue`，因此STL中采用`deque`作为`queue`的底层实现。

#### 4.6.3 queue没有迭代器

由于只允许读及取队头、写队尾，因此queue不允许遍历访问其他任何元素。也没有迭代器。

#### 4.6.4 以list作为queue的底层容器

书中代码在P171，展示以`list`作为`queue`的底层容器，同样没有任何特色，在此不做解释。

### heap(隐式表述的容器)

#### 4.7.1 heap概述

heap本身并不是STL的容器组件，而是作为`priority queue`的助手被应用。

优先队列允许以任意次序将元素插入队列中，但是取出时总是以优先级（数值大小）的元素开始取。这意味着如果我们采用类似`list`的方式来实现优先队列，在插入或者取出元素时至少有一个操作需要$O(n)$的时间复杂度来完成，这样效率并不高。

一种解决办法是使用二叉搜索树作为优先队列的底层实现，这样做的话的确可以实现$O(\log{N})$的插入和取极值的表现，但是这要求输入数据具有足够的随机性（如果输入数据是递增序的，那就是一棵很不平衡的树了），另一方面难以实现。

因此，`binary heap`（二叉堆）就成为了适当的选择。`binary heap`是一种完全二叉树，所谓完全二叉树指的就是除了最底层的叶子节点以外，所有节点都是填满的。而最底层的叶子节点又不会有空隙（不存在某个叶子节点只有右子树没有左子树）。

由于完全二叉树没有任何的漏洞，因此仅仅使用一个`array`就可以存储所有的节点了。而如果我们把`array[0]`保留不做使用，从下标$[1]$开始存储完全二叉树，那么:<font color="red">当完全二叉树的某个节点处于`array[i]`时，它的左子树一定在`array[2i]`，右子树一定在`array[2i + 1]`，父节点一定在`array[i / 2]`。</font>

这样一来，我们仅仅需要一个`array`和一组`heap`算法（用来插入元素、删除元素、取极值、将一整组数据排列成heap）就可以实现`priority queue`了。但是`array`无法动态改变大小，`heap`需要这一功能，因此采用`vector`来代替`array`。

根据元素的排列方式，heap又可以分为大根堆和小根堆。顾名思义，大根堆就是较大的值作为根节点，它的左右子节点的值都比它小，因此极大值处于根节点。小根堆情况类似，只不过是极小值处于根节点。在底层实现中，这意味着极值处于`vector[1]`的位置。



书中后续提到的堆，指的都是大根堆。

#### 4.7.2 heap算法

##### push_heap算法

为了满足完全二叉树的条件，新加入堆的元素必定作为叶子节点放在最下面一层，并且填补从左至右的第一个没有叶子的位置处（这里如果看不懂就看书上P174的图），也就是把元素插入在`vector()`的`end()`处。

但是插入的元素并不一定符合大根堆的要求（根节点比左右子树的值都大）。因此插入叶子节点后，还需要执行一个上溯程序:<font color="red">将新的节点拿来与父节点进行比较，如果其值大于父节点，就交换二者。重复这个过程直到不需要对换，或者直到新节点成为根节点为止。</font>

书中代码在P175，这里给出简单解释：

首先，我们事先得到一个前提：调用`push_heap`时，新加入的元素已经在`vector`的尾部。

`push_heap`内部转调用`__push_heap_aux`，同时萃取出迭代器以及值的类型。

`__push_heap_aux`内部再次转调用`__push_heap`，参数分别是：

- `first`，表示底层容器(`vector`)的起始元素位置。
- `Distance(last - first - 1)`，表示最后插入的元素的下标。
- `Distance(0)`，表示起始元素的下标。
- `T(*(last - 1))`，最后插入的元素值。

转调用后，在`__push_heap`函数的内部，首先计算出最后插入元素的父节点（`vector[i / 2]`），然后循环判断是否大于父节点，不断执行交换操作直到不满足条件为止。

#### pop_heap算法

> 事后补充：
>
> 这里其实还是看明白了，实际上也和下面说的差不多，只不过书上描述的方式有点笼统。
>
> 首先，还是将最后一个元素覆盖根节点。根节点的元素被放在了vector中堆的部分的后面。
>
> 然后，对新的根节点（原来的最后一个叶子节点）执行下沉操作，将其与左右子节点的值进行比较并交换，重复这个过程即可满足大根堆的性质。

这里书中给出的图（P176）看的并不是特别明白，但是大概能描述发生了什么过程：

当我们要从堆中取出极大值时，相当于要取出大根堆的根节点，这不仅导致整个堆的最大值没有了，也使得根节点的左右子树都失去了父节点（极大值），因此必须调整堆使得其重新满足大根堆的位置。

这里很朴素的想法是，既然大根堆的极大值在根节点，那么不就意味着它的左右子节点就是"候选者"吗？新的极大值一定在它们二者中产生。只要让它们二者之一成为新的根节点就好了。

这个想法其实没有错，但是考虑的不够完全。假设原根节点的右子节点成为了新的根节点，假如它也有子节点呢？这意味着以它为父节点的子节点失去了极大值。

也许我们会觉得，继续执行这个操作，让两个子节点之一接替原根节点的右子节点即可。这实际上并没有解决问题，只是延后了问题。因为到了倒数第二层的时候（书中P176给出的例子就是），如果从子节点中取出一个值接替父节点，那么就会使得堆不满足完全二叉树的性质。

这个问题被描述的有点复杂了，其实解决很简单。

考虑在一个`vector`中，如果要取出最前面的元素，假设我们并不想移动整个`vector`，那么取出最前面的元素，

再用最后的元素覆盖最前面的元素的位置，然后令`vector`的size - 1即可。

整体描述起来就是，用最后一个元素值覆盖大根堆的根节点的值。然后执行"下溯"：不断将根节点的值与左右节点中的值进行比较，并与较大的值交换，重复这个过程直到重新构建成堆即可。

书中代码在P177，这里给出简单解释：

`pop_heap`方法负责萃取出迭代器指向的值类型，转调用`__pop_heap_aux`。

`__pop_heap_aux`，此函数调用的一个前提是"根节点的值被调整到整个vector"的`end()`位置，然后转调用`__pop_heap`。

`__pop_heap`设定返回值为`end()`位置的值，然后转调用`__adjust_heap`来调整`[begin(), end() - 1)`范围的值。

`__adjust_heap`负责比较左右子节点，调整位置。这里稍微值得注意的就是需要判断是否具有左右子节点（二者之一没有的话肯定就是没有右子树，不存在有右子树没有左子树的情况，毕竟完全二叉树）

##### sort_heap

内部调用`pop_heap`，代码在书中P178.

这里能够调用`pop_heap`的原因还是因为实质上`pop_heap`没有删除元素，只是把元素堆在了`vector`的表示堆的部分的后面，并不复杂。

显然，多次调用`pop_heap`后会在`vector`中得到一个递增序列。

##### make_heap

这个算法用于将一段序列数据转换为一个堆，代码在书中P180。

这段代码的原理很简单，仅仅给出简单解释。

其实就是对所有"非叶子节点"执行下沉操作，从最后一个非叶子节点开始，直到根节点结束。不断调用`__adjust_heap`即可完成。

#### 4.7.3 heap没有迭代器

当然了，heap本身是一种特殊的排列方式，它不需要进行遍历，自然也不提供迭代器了。

#### 4.7.4 heap测试实例

书中代码在P181，只是一段测试代码。

### 4.8 priority_queue

实际上就是大根堆实现的，没啥特色，在此不赘述，代码在书中P183。

### 4.9 slist

#### 4.9.1 slist概述

`slist`实际上是`single list`的缩写，也就是单向链表。它并不是STL标准库中的实现，而是SGI STL的特供。因此这部分也不会花太大心思做笔记，简单了解。

为什么要有`slist`？明明已经有了`list`实现了，而且`list`作为环状双向链表提供了双向迭代，作为单向链表只能`Forward iteration`，原因在于它使用的空间更小，某些操作更快。

值得注意的是，根据STL的习惯，`insert`函数实现的插入操作，实际插入的位置在插入点之前，也就是说假如我们的插入点为`x`，那么插入时我们需要修改`x.prev.next`、`x.prev`、`x.next`和`x.next.prev`。作为单向链表显然没有`prev`指针，因此只能通过`while(node.next != x)`这样的方式来找到`x.prev`，显然这样太慢了。

因此`slist`特别提供了`insert_after()`和`erase_after()`来实现插入和擦除的操作。

#### 4.9.2 slist的节点

`slist`的节点实现有一点奇怪，它定义了一个名为`__slist_node_base`的类，其中只包含一个指针，表示单向链表的下一个节点。

然后，它定义了一个模板类:

```cpp
template<class T>
class __slist_node : public __slist_node_base{
	T data;
};
```

我并不理解为什么它要这样设计，而不是在一个类中同时包含`data`和`next`指针。

> 这种设计模式被称为基类/派生类策略，它在STL中的很多地方都有应用。这样设计的原因主要有以下几点：
>
> 1. **类型无关的操作**：通过将节点的链接部分（即`next`指针）放在一个非模板的基类`__slist_node_base`中，可以对链表进行一些类型无关的操作，如插入、删除等，而不需要知道节点中数据的具体类型。这样，一些通用的、与数据类型无关的操作可以在基类中实现，而不需要为每种数据类型都生成新的代码。
>
> 2. **代码复用**：由于很多单向链表的操作与节点中的数据类型无关，所以可以在`__slist_node_base`中实现这些操作，然后在所有的`__slist_node<T>`中复用这些操作。这样可以减少代码的重复和模板代码的生成。
>
> 3. **编译时间优化**：模板会为每种数据类型生成新的代码，这可能会增加编译时间和生成的代码的大小。通过将一些与数据类型无关的操作放在非模板的基类中，可以减少模板代码的生成，从而优化编译时间和生成的代码的大小。
>
> 4. **灵活性**：这种设计提供了更大的灵活性，允许在基类中添加新的成员或方法，而不影响派生类。同时，也可以在派生类中添加新的成员或方法，以提供更多的功能。
>
> 总之，这种设计模式可以提高代码的复用性、减少模板代码的生成、优化编译时间和生成的代码的大小，并提供更大的灵活性。这也是为什么STL中的很多容器都采用了这种设计模式。

#### 4.9.3 slist的迭代器

没有太大的特色，代码在P188，不做解释。

#### 4.9.4 slist的数据结构

代码在P190，也就是普通的单向链表实现，不做解释。

#### 4.9.5 slist的元素操作

代码在P191，同上。。

## 5. 关联式容器

根据"数据在容器中的排列方式"，容器分为序列式容器和关联式容器，本章讨论关联式容器。

标准的关联式分为`set`（集合）和`map`（映射）两大类，以及它们的衍生物`multiset`等。这些容器底层均以红黑树（`RB-Tree`）进行实现。红黑树也是一个独立容器，但并不开放给外界使用。

一般而言，关联式容器的内部结构时一个balanced binary tree（平衡二叉树），平衡二叉树包含许多种类型（`AVL-Tree`、`RB-Tree`、`AA-Tree`等）。

### 5.1 树的导览

书中P199介绍了概念，在这不多赘述。

#### 5.1.1 二叉搜索树

所谓二叉搜索树，可以提供对数时间的元素插入和访问。它的节点放置规则是：任何节点的键值一定大于它左子树中每一个节点的键值，并且小于其右子树中每一个节点的键值。

要在二叉搜索树中插入元素，只要从根节点开始逐个将插入元素和节点值进行比较，如果节点值大于插入元素值，则前往其左子树，否则前往其右子树。重复这个过程直到某个节点的左子树或者右子树为空时，将插入元素插入到对应的位置即可。

要在二叉搜索树中删除元素，情况分为两种：

- 删除元素包含左右子树，此时我们应该让某个节点接替被删除的节点。谁是这个节点呢？考虑二叉搜索树"左子树所有节点小于当前节点值，右子树所有节点大于当前节点值"。我们应该找到被删除的节点的右子树中的最小值（右子树中最左边的节点），将它替换到被删除的节点的位置。
- 删除元素不包含子树，或者只有一边子树。如果删除的节点是叶子节点，那当然没什么好说的。如果只有左子树或者右子树，答案也很简单，让子树的根节点替代被删除的节点即可。

#### 5.1.2 平衡二叉搜索树

由于输入不够随机（假设输入保持一个递增序），可能会导致二叉搜索树非常"不平衡"。

"平衡"的大致意义是：没有任何一个节点深度过大（其实我印象中学过的定义说的是，对于任何节点的左右子树，它们的深度差不大于某个值）。

#### 5.1.3 AVL Tree

`Adelson-Velskii-Landis tree(AVL tree)`，这是一种自平衡二叉树。也是我刚刚提到的概念中"对于任何节点的左右子树，它们的深度差不大于某个值"。

AVL Tree要求，对于任何节点的左右子树，它们的深度差不超过1。这样可以保证对数深度$O(\log{N})$的平衡状态。

在常规的二叉搜索树上，当我们插入的元素不具备足够的随机性时，则可能导致树不平衡。这意味着某个节点的左右子树的深度差大于等于2。

AVL Tree调整树使其获得平衡的策略是:<font color="red">调整从"插入点到根节点"的路径上，平衡状态被破坏的各个节点中最深的那一个。换而言之，就是找到左右子树深度差最大的那个节点，调整它就可以重新获得平衡。</font>

而从深度差最大的那个节点出发，破坏平衡的新节点的位置有四种情况:

- 新节点处于深度差最大节点的左子节点的左子树 --- 左左
- 新节点处于深度差最大节点的左子节点的右子树 --- 左右
- 新节点处于深度差最大节点的右子节点的左子树 --- 右左
- 新节点处于深度差最大节点的右子节点的右子树 --- 右右

其中，第1和第4种情况彼此是对称的，可以采用单旋转操作调整解决。第2和第3种情况是彼此对称的，可以采用双旋转操作调整解决。

#### 5.1.4 单旋转

正如上面所说的，单旋转操作调整的是第1和第4种情况。假设出现的是第1种情况，如果从深度差最大节点出发来看，我们拥有一棵这样的树：

- 左子树的深度为3或更大
- 右子树的深度比左子树小2或更多

书中P205就展示了这样的一种情况。

在这样的情况下，假如深度差最大节点的左右子树深度相差2。很自然的一个想法就是：把左子树的深度减少1，同时把右子树的深度加上1。这样就完全达到了抵消深度差的效果。

单旋转做的就是这样的事，它将<font color="red">深度差最大的节点(后称根节点)"向右旋转90度，使得根节点的左子节点成为新的根节点"。</font>

这有点像把原根节点的左子节点"提起来"，那么原根节点自然因为更"重"而成为了新根节点的右子节点。

但是还有一种情况要处理，既然原根节点因为更重成为了新根节点的右子节点，原根节点也因此失去了左子节点（原根节点的左子节点就是新的根节点）。新根节点的右子节点成了原根节点，那新根节点如果有原右子节点呢？

答案也很简单，新根节点的原右子节点的"重量"一定是小于原根节点的（要不然怎么会在原根节点的左子节点上），因此让新根节点的原右子节点成为原根节点的新左子节点即可。

这样就完成了左左情况下单旋转的操作，对于右右的情况处理也是类似的。

#### 5.1.5 双旋转

双旋转调整的是第2和第3种情况，书中P207展示了第2种情况，第3种情况的解决办法也是一样的。

为什么要双旋转？单旋转不能解决问题了吗？答案是肯定的，因为现在破坏平衡的节点处于<font color="red">深度差最大的节点的左子节点的右子树上（右左的情况和它对称）。</font>如果仍然采用单旋转的方式，将原根节点的左子节点的右子树链接到新的根节点的右子节点的左子树上，那么深度差仍然是存在的，只是把"左右"的情况变成了"右左"而已（画图可验证）。

下面以书中的例子作为范本进行讲解，具体需要结合书上看。

单旋转为什么解决不了问题？关键问题还是在于，左左情况下的单旋转会将新的根节点的左边深度减去1，右边深度加上1（右边新增的深度来自原根节点）。但是<font color="red">新的右子节点的左子树上还要链接新的根节点的原右子树</font>，在"左右"的情况下，破坏平衡的节点就处在这里，把它链接到新根节点的右子节点的左子树上只是把"左右"情况变成了"右左"而已。

因此，关键的问题还是在于，不能让单旋转时，左子节点的右子树还在，影响到单旋转后的新右子节点。

方法就是<font color="red">以原根节点的左子节点作为根节点（对这个节点而言，它的子树是平衡的），向左旋转90度做一次单旋转。使得根节点的右子树成为新的根节点，且将破坏平衡的节点从新根节点的右子树上挪开。然后再以原根节点（指的是深度差最大的那个）进行一次单旋转向右旋转90度，就能得到一棵新的平衡树了。</font>

这里的文字描述还是太模糊了，具体还是看书上的图结合来理解。比较好理解。

### 5.2 RB-Tree(红黑树)

红黑树，不仅是一个二叉搜索树，而且必须满足以下规则：

1. 每个节点不是红色就是黑色。
2. 根节点为黑色。
3. 如果节点为红，其子节点必须为黑。
4. 任意节点至NULL的任何路径，所含黑节点数必须相同。

> 红黑树是一种自平衡的二叉搜索树，它通过这些规则来保持树的平衡。这些规则的目的是为了确保在插入、删除和查找操作时，树的高度保持在一个相对较低的水平，从而提高操作的效率。下面我们来分析这些规则的作用：
>
> 1. 每个节点不是红色就是黑色：这个规则为后续规则的应用提供了基础，通过对节点进行着色，我们可以控制树的结构。
>
> 2. 根节点为黑色：这个规则保证了从根节点到叶子节点的最长路径不会超过最短路径的两倍。因为红色节点的子节点必须为黑色，所以最短路径全为黑色节点，而最长路径则是黑色节点和红色节点交替出现。
>
> 3. 如果节点为红，其子节点必须为黑：这个规则避免了连续的红色节点出现，从而确保了从根节点到叶子节点的最长路径不会超过最短路径的两倍。
>
> 4. 任意节点至NULL的任何路径，所含黑节点数必须相同：这个规则确保了所有从根节点到叶子节点的路径上黑色节点的数量相同，从而使得树保持大致平衡。
>
> 通过这些规则，红黑树在插入、删除和查找操作时，能够保持较低的树高，从而提高操作效率。在最坏情况下，红黑树的高度为$2\log(n+1)$，其中n为节点数量。这使得红黑树在很多场景下成为一种非常高效的数据结构。

根据规则4，新插入的节点必定是红色节点（因为如果插入节点为黑色，则插入的这个节点所在的路径上的黑色节点会多一个，违反了规则4）。

根据规则3，新增节点的父节点必定是黑色。因为新增的节点必定是红色的，如果父节点是红色的，那么父节点就违反了规则3。

如果新节点根据二叉搜索树的规则到达其插入点，但是上述条件不能被满足时，就必须调整颜色并旋转树型。

#### 5.2.1 插入节点

这里给出了一个例子，具体在书中P209，这里给出个人理解的描述。

首先，我们要为一些节点定义名称。

- 新插入的节点名为`X`
- 新插入节点的父节点名为`P`
- 新插入节点的祖先节点（父节点的父节点）为`G`
- 新插入节点的父节点的兄弟节点为`S`
- 新插入节点的曾祖节点（父节点的祖先节点）为`GG`

首先，根据二叉搜索树的规则，新插入的节点必定是叶子节点。

那么，根据规则4，新插入的节点`X`必定是红色节点。注意，插入时并不一定保证插入后红黑树规则不被违反，可能需要在插入前改变树形。因此，`X`的父节点`P`有两种情况：

- `P`为红色节点，则`P`违反了规则3，但同时也说明`P`的父节点`G`必定是黑色节点。
- `P`为黑色节点，则可以正常插入`X`。

因此，根据`X`的插入位置（指的是满足哪种旋转的情况）以及`S`和`GG`的颜色，有这些状况：

1. `S`为黑色，且`X`的插入位置为左左或右右。

​		此时

2. 

**<font color="red">这部分内容不再做笔记，因为基本都需要看着书才能理解，写笔记也只是抄书。要复习看书上P209.</font>**

**<font color="red">2023.11.06，红黑树暂时没法理解，太复杂了，得找个时间专门学习。不知道面试会不会问，因此暂时不花太多时间学习这么复杂的内容，以免后面忘记。后面有时间再看。</font>**

---

### 5.3 set

集合是一种无重复元素的容器，它的键值就是它的实际值，因此不能通过迭代器来改变它的值。

`set`的迭代器底层使用`RB-Tree`的`const-iterator`来实现，因此拒绝任何写入操作，标准的STL`set`也是以`RB-Tree`作为底层机制。

下面是关于`set`实现的描述，书中代码在P233，这里给出简单解释：

首先还是给出一些别名定义，可以注意到将键和值的类型定义为同一类型，并使用同一个比较器，这点的原因在上面说的很清楚了，`set`的键和值就是一回事。

然后，定义了一个红黑树来作为`set`的底层实现，这个定义中模板参数分别包含了：键的类型、值的类型、原始值类型、比较器、内存分配器。

随后又是一些常规的`value_type`以及`iterator`的别名定义，用于萃取操作。

之后，定义了几种不同的`set`构造函数，这部分没太多好说的。

然后就是`set`的操作了，由于底层采用`RB-Tree`进行实现，所以这里所有的操作实际上都是转调用`RB-Tree`的方法，没有太多值得说的。

### 5.4 map

`map`的特性在于，所有元素都会根据元素的键值自动被排序。

`map`的键值实际上是一个`pair`，它的`first`和`second`属性中分别保存着键和值。排序时按照键进行排序。

`map`的底层也采用了`RB-Tree`作为实现，因此几乎所有的`map`操作行为，底层都是转调用`RB-Tree`的操作行为。

书中代码在P239，这里仍然给出简单的解释。

首先，`map`区别于`set`的一点就是，它的键和值可能是不同的类型。因此`map`的模板类定义中需要为键和值分别设置模板参数。

然后，定义的起始处仍然是为键和值等分别定义别名，并定义比较函数用于排序。

然后，定义一个`RB-Tree`类型的属性用于`map`的实现，然后萃取出它的属性。

之后就是`map`的一些构造函数定义和实现了，实现基本上都是对于`RB-Tree`方法中的转调用，因此不过多解释。

值得注意的一点是，`map`的`insert`函数转调用`RB-Tree`的`insert_unique`执行，因此其返回值类型是一个`pair`，其第一个参数表示一个指向插入元素的迭代器，第二个参数是一个`bool`类型，表示插入操作是否成功。只有在插入成功时，第一个参数才指向插入元素。

另外一个值得注意的是下标运算符，它既可以作为左值使用，也可以作为右值使用：

```cpp
map<string, int> simap;
simap[string("jjhou")] = 1;	//左值使用
...
int number = simap[string("jjhou")]; // 右值使用
```

当它作为左值使用时，意味着它可修改。但是它作为右值使用时，意味着它不可修改。适用二者的关键在于，<font color="red">返回值以引用的形式进行传递。</font>

这部分书中代码在P243，这里只给出关键的一行：

```cpp
return (*(insert(value_type(k, T())).first)).second;	// 注意，函数定义中返回的是引用类型
```

第一眼看上去我人晕了。。

下面一步步进行拆解：

- `value_type(k, T())`，注意的是，这里的`value_type`实际上是`pair`类型，因此这行代码以`k`和临时对象`T()`作为参数调用`pair`的构造函数，产生一个`pair`对象。为什么要以临时对象`T()`作为参数调用来产生`pair`对象？这是因为我们无论以左值还是右值的方式使用`[]`下标运算符时，我们都是不知道实际的值的。
- `insert(value_type(k, T))`，这一行就很简单了，调用`insert`函数将`pair`对象插入到`map`中，并返回一个`pair`表示一个指向插入节点的迭代器和插入操作是否成功的`bool`。
- 假设`insert`函数返回的是`p`，那么接下来就是`p.first`，得到指向新插入节点的迭代器。
- `*(p.first).second`，得到迭代器指向的值（新节点），并得到新节点的值的引用，返回这个引用。

返回了这个引用后，它既可以作为左值使用进行赋值，也可以作为右值使用进行传值了。

### 5.5 multiset

和`set`几乎完全相同，只是因为`multiset`允许值重复。因此`insert`函数转调用的是`insert_equal`而不是`insert_unique`。

### 5.6 multimap

和上面同理，也只有`insert_equal`不同。

### 5.7 hashtable

#### 5.7.1 hashtable概述

hash table可以提供对任何named item的存取和删除操作，由于操作对象是named item，因此hashtable也可以视作一种字典结构。

> 在这个语境下，"named item"指的是哈希表中的一个元素，这个元素有一个特定的名称或者说键（key）。在哈希表中，每个元素都是一个键值对，键是唯一的，用于标识和访问这个元素，值则是与这个键关联的数据。所以，"named item"就是指这样的一个键值对。

字典结构的用意在于，提供常数时间的读写操作。例如桶排序就是一种提供了常数时间读写的算法。

但是类如桶这样的方法存在的问题在于，桶受到大小的限制，如果桶过大势必有大量内存浪费。而且桶也要求以数值类型作为索引，因此无法接受其他类型来索引。

可能有人会觉得，只要将字符串（或者其他类型）转换成数值类型就好了。但是实际上也受到了索引本身大小的限制，如果一个过长的字符串，同样会被映射成一个非常大的索引（例如`57348958923749836`这样的索引），显然这也是不能接受的。

那么如何解决呢？方法就是使用一个映射函数（映射并非直接的转换）将大数映射为小数，将某个元素映射成"大小能接受的索引"，这样的函数称为散列函数（或者说哈希函数？）。

但是哈希函数最常见的问题当然就是哈希碰撞了，解决的方法有线性探测、二次探测、开链等方法，这些方法都比较容易，效率并不相同，与哈希表本身被填满的程度有很大的关联。

##### 线性探测

负载系数(`loadingn factor`)，计算方式为`已有元素个数 / hash表的大小`，它一定是一个`[0, 1]`范围内的数字，除非采用开链的方式。

线性探测的方法就是，当哈希函数计算出某个元素的插入位置，但是那个位置已经有一个元素时，就随着后面往下查找，直到找到一个可用的位置插入进去，但是这样的话，要花多少时间进行插入就很难说了。

至于元素的删除，就只能采用惰性删除的方式，只标记一个删除记号，但是实际删除操作必须等到表格重新整理再进行。

线性探测的表现不佳，主要因为其可能带来"主集团"问题，即平均插入成本的成长幅度（平均插入成本指的就是查找插入位置和插入花费的时间）远大于负载系数增长的速度。

##### 二次探测

二次探测主要就是解决了线性探测的主集团问题。

假设哈希函数计算出的插入位置为`H`，而该位置已经有元素。按照线性探测的方式，它会继续尝试`H+1`、`H+2`、`...`直到找到合适的空位置。

而二次探测则是探测`H+1²`、`H+2²`、`...`这些位置。

二次探测的好处在于，如果我们假设表格大小为质数，且负载系数超过0.5时就整理表格，那么能够保证每插入一个新元素时所需要的探测次数不超过2.

二次集团可以消除主集团问题，但却可能造成次集团问题：两个元素如果经过哈希函数计算出的位置相同，那么插入时探测的位置也相同，形成某种浪费。消除次集团的方法有诸如复式散列等。

##### 开链

开链就是在每个表格元素中维护一个`list`，我们实际插入的元素在`list`中。虽然对`list`只能进行线性查找等操作，但是只要`list`没那么大，速度还是很快的。

使用开链方法的话，哈希表的负载系数将超过1。

#### 5.7.2 hashtable的桶与节点

SGI STL中采用的哈希表实现，使用的就是开链的方法。

因此，hashtable内的每个单元，并不一定只是一个节点，而可能是一个"桶"，包含了一桶节点。

书中P253给出了`hash table`的节点定义，实际上就是一个典型的链表定义。而包含了众多节点的`hash table`，则是采用具有动态扩充能力的`vector`进行实现。

#### 5.7.3 hashtable的迭代器

hashtable提供的是`forward iterator`，因为它的"一桶节点"是一个单向链表。

书中代码在P254，这里给出简单解释。

首先，仍然是一些别名的定义，没什么好说的。

然后，定义了一些`traits`用于萃取。

此后，定义了一个指针指向迭代器当前应该指向的节点，以及一个指向整个`hashtable`的指针，因为我们可能需要从一个桶跳转到另一个桶，所以我们应该持有这样的`hashtable`指针。

此外，就是定义了一些常规的迭代器运算了，没有特别值得好讲的。

整个迭代器提供一个前向迭代功能，假如迭代器当前指向某个桶中的某个节点，向前迭代将会使得迭代器指向下一个节点。

如果已经到达了某个桶的尾端，没有下一个节点。则向前迭代会使得迭代器指向下一个桶的第一个节点。

#### 5.7.4 hashtable的数据结构

`hashtable`包含了好几个模板参数，包括：

- 节点的值类型`Value`
- 节点的键类型`Key`
- 哈希函数的函数类型`HashFcn`
- 从节点中取出键和值的方法`ExtractKey`，这是一个函数或仿函数
- 判断键值是否相同的方法`EqualKey`，这也是一个函数或者仿函数
- 空间配置器`Alloc`，默认使用`std::alloc`

SGI STL以质数来设计哈希表的大小，虽然开链法并不要求表格大小为质数。

#### 5.7.5 hashtable的构造与内存管理

这部分代码在P258，这里给出简单解释。

当我们初始构造一个拥有50个节点的哈希表时，实际构建的大小是大于50的第一个质数，也就是53个元素大小的哈希表，然后将其中所有的桶（也是第一个节点）全部填充为空指针。

##### 插入操作与表格重整

当我们插入元素时，首先判断是否需要重建表格，如果需要重建表格，那么就对哈希表的大小进行扩充。

判断是否需要重建哈希表的规则比较奇特，但是可以理解，这条规则是"如果将新增的节点插入到哈希表后，哈希表中包含的元素数量超过了桶的数量，那么就重建表"。

这条规则意味着由元素在桶中构成的链表总长度不能超过实现桶的`vector`的长度，同时另一重含义是"如果插入元素都在一条链表上，那么这条链表最多能和桶一样长，这将造成查找时线性查找，同样浪费了时间"。

1. 如果真的需要重建哈希表，新的哈希表将是一个"约为原大小两倍的质数"大小的哈希表。

​		重建哈希表相当于"在别处分配了一大块内存"，因此需要将旧的数据移动过去。这里移动的方式需要简单解释一下，使用循环的方式遍历每一个节点：

- 首先，判断节点在新的哈希表中处于哪个桶中。这是因为节点在旧的哈希表中可能由于哈希碰撞的原因处在某个桶中，但是它在新的哈希表中的位置不一定相同。

  >在哈希表中，元素的位置是由哈希函数和哈希表的大小共同决定的。当你将元素从一个小的哈希表移动到一个更大的哈希表时，即使哈希函数没有改变，元素的位置也可能会改变。
  >
  >这是因为哈希函数通常会生成一个相对较大的哈希值，然后我们会用这个哈希值对哈希表的大小取模，得到元素在哈希表中的位置。当哈希表的大小改变时，取模的结果也可能会改变，因此元素的位置也可能会改变。
  >
  >这种改变是有意为之的，因为当哈希表变大时，我们希望元素能够更均匀地分布在哈希表中，以减少哈希冲突，提高哈希表的性能。

- 然后，以头插法的形式将元素插入到新的哈希表中。

- 接着指向下一个节点，继续重复上述操作。

​		在上述循环完成以后，我们交换指向旧的哈希表的指针(`vector *`)和新的哈希表的指针，使用`swap`函数。然后，由于函数作用域的原因，旧的哈希表的内存区块将会随着局部变量`vector tmp`一起释放。

2. 如果不需要重建哈希表，那么以不重复的`insert_unique`插入节点时，在插入一个新节点时，首先计算它哈希后所处的桶。然后我们需要事先遍历一遍这个桶，如果桶中有相同的元素，则会退出返回一个`pair`，第一个元素是一个指向该相同元素的迭代器，第二个元素是`bool`变量`false`，表示插入操作失败了。

​		如果桶中没有相同的元素，则以头插法的方式将元素插入到链表头部。并返回插入成功的`pair`。

​	另一种情况是以可重复的`insert_equal`插入元素，所做的行为大致相似，只不过在循环查找元素时，如果找到了相同的元素，则立即将新元素插入到相同的元素之后并返回。否则同样按照头插法的方式将新元素插入到链表头部。

##### 判断元素所在的桶

这个函数名为`bkt_num`，这本来是哈希函数应该做的事（哈希函数返回的值就是新元素应该在的桶）。只不过STL将其做了一层包装，由该函数转调用哈希函数。

为什么要这么做？因为有些类型（比如`char *`字符串）不能直接将其对哈希表的大小进行模运算。因此需要转调用先进行哈希，再进行模运算。包装统一了这样的行为。

##### copy和clear

整个hashtable由`vector`和单链表构成，因此复制和删除都需要注意内存释放的问题。

这部分代码在书中P263，这里进行简单解释。

首先来看`clear`函数，该函数其实就是逐个遍历所有桶中的所有元素，逐个使用delete将其释放。但是该操作只是删除了所有元素，容纳所有桶的`vector`仍然存在。

再来看看`copy_from`函数，该函数从参数所在的哈希表中将它的元素全部复制到调用的哈希表对象中。

首先，清空自身哈希表的内容。然后，比较自身和参数哈希表的大小，如果自身大小更大，则不做改变，否则将对自身进行扩容。

然后，将自身哈希表中的每个桶中插入一个空指针。

之后，循环将参数哈希表中的每个桶中的每个节点逐个复制过来（仍然是头插法）。

最后不要忘记更新哈希表中保存的元素个数`num_elements`。
