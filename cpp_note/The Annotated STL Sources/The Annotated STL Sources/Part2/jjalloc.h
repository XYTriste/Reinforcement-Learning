#ifndef _JJALLOC_
#define _JJALLOC_

#include<new>
#include<cstddef>
#include<cstdlib>
#include<climits>
#include<iostream>

namespace JJ {

	template<class T>
	inline T* _allocate(ptrdiff_t size, T*) {	// �����ڴ�ĺ���������ɹ�ʱ�������ڴ����ʼ��ַ
		std::set_new_handler(0);			// ����Ĭ�ϵ��쳣���������ڴ����ʧ��ʱ�����׳�std::bad_alloc�쳣
		T* tmp = (T*)(::operator new((size_t)(size * sizeof(T))));	// ���Է���size * sizeof(T)�ֽڴ�С���ڴ�
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
	inline void _construct(T1* p, const T2& value) {	// ���ѷ�����ڴ��Ϲ������
		new(p) T1(value);		// ʹ�ö�λnew�������ָ�����������λ��
	}

	template<class T>
	inline void _destroy(T* ptr) {	// ���ٴ����Ķ���
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

		/*allocator() = default;

		template<class U>
		allocator(const allocator<U>&) {}*/
		template<class U>
		struct rebind {
			typedef allocator<U> other;
		};

		//hint used for locality
		pointer allocate(size_type n, const void* hint = 0) {
			return _allocate((difference_type)n, (pointer)hint);
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