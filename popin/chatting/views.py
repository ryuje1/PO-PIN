from django.shortcuts import render, redirect
from django.http import JsonResponse,HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
import json
from django.utils import timezone

from .models import ChatMessage, ChatRoom
from photocard.models import Photocard
from community.models import ProxyPost, CompanionPost
from community.models import Board
from signupFT.models import User, UserRelation


def chatting(request):
    
    user_id = request.session.get('user_id')  # 로그인 시 저장한 user_id 세션

    if not user_id:
        return redirect('login:loginp')

    try:
        user = User.objects.get(user_id=user_id)
        rooms = ChatRoom.objects.filter(host_user=user) | ChatRoom.objects.filter(guest_user=user)
        rooms = rooms.distinct().order_by('-last_timestamp').exclude()  # 최근 채팅 순 정렬
        first_room = rooms.first()
        messages = ChatMessage.objects.filter(room=first_room).order_by('timestamp')

        room_list = []
        for room in rooms:
            # 기존 교환/판매 관련 로직 유지
            if hasattr(room, 'category') and room.category in ("exchange", "sale"):
                post = Photocard.objects.get(pno=room.post_id)
                if post.sell_state == "후" and post.buy_state == "후":
                    continue
                else:
                    read_count = ChatMessage.objects.filter(
                        room=room,
                        is_read=False
                    ).exclude(send_user=user).count()
                    if user.nickname == room.host_user.nickname:
                        nickname = room.guest_user.nickname
                        user_id = room.guest_user.user_id
                    else:
                        nickname = room.host_user.nickname
                        user_id = room.host_user.user_id

            elif room.category == "companion":
                post = CompanionPost.objects.get(id=room.post_id)
                if post.status == "완료":
                    continue
                else:
                    read_count = ChatMessage.objects.filter(
                        room=room,
                        is_read=False
                    ).exclude(send_user=user).count()
                    if user.nickname == room.host_user.nickname:
                        nickname = room.guest_user.nickname
                        user_id = room.guest_user.user_id
                    else:
                        nickname = room.host_user.nickname
                        user_id = room.host_user.user_id
            elif room.category == "proxy":
                post = ProxyPost.objects.get(id=room.post_id)
                if post.status == "완료":
                    continue
                else:
                    read_count = ChatMessage.objects.filter(
                        room=room,
                        is_read=False
                    ).exclude(send_user=user).count()
                    if user.nickname == room.host_user.nickname:
                        nickname = room.guest_user.nickname
                        user_id = room.guest_user.user_id
                    else:
                        nickname = room.host_user.nickname
                        user_id = room.host_user.user_id        
            room_list.append({
                'id':room.id,
                'category': room.category,
                'post':post,
                'user_id':user_id,
                'nickname': nickname,
                'last_timestamp':room.last_timestamp,
                'last_message' : room.last_message,
                'read_count' : read_count,
            })

        context = {
            'rooms': room_list,
            'messages': messages,

        }

        return render(request, 'chatting/chatting.html', context)

    except User.DoesNotExist:
        return redirect('login:main')

def test(request):
    return render(request, 'chatting/test.html')

def start_chat(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST만 허용됩니다.'}, status=405)
    
    try:
        body = json.loads(request.body)
        category = body.get('category')
        post_id = body.get('post_id')
        
        print(category, post_id, flush=True)
        
        user_id = request.session.get('user_id')  # 현재 로그인한 사용자
        if category == "exchange" or category == "sale":
            try:
                guest_user = User.objects.get(user_id=user_id)
                post = Photocard.objects.get(pno=post_id)
                post.buyer = guest_user
                post.buy_state ="중"
                post.save()
                
                room, created = ChatRoom.objects.get_or_create(
                    category=category,
                    post_id=post.pno,
                    host_user=post.seller,
                    guest_user=post.buyer,
                    defaults={
                        'last_timestamp':now(),
                        'last_message' : "채팅을 시작해 보세요",
                    }
                )
                
                return JsonResponse({'success': True, 'created':created, 'room_id': room.id})
                
            except User.DoesNotExist:
                return redirect('home:main')  # 예외 상황 대비
            
            except Exception as e:  
                print(e)
                return JsonResponse({'error': str(e)}, status=500)
            
        elif category == "companion":
            try: 
                guest_user = User.objects.get(user_id=user_id)
                post = CompanionPost.objects.get(id=post_id)
                post.participants.add(guest_user)
                post.save()
                if post.participants.count() == post.max_people:
                    post.status ="모집완료"
                post.save()
                
                room, created = ChatRoom.objects.get_or_create(
                    category=category,
                    post_id=post.id,
                    host_user=post.author,
                    guest_user=guest_user,
                    defaults={
                        'last_timestamp':now(),
                        'last_message' : "채팅을 시작해 보세요",
                    }
                )
                
                return JsonResponse({'success': True, 'created':created, 'room_id': room.id})
                
            except User.DoesNotExist:
                return redirect('home:main')  # 예외 상황 대비
            
            except Exception as e:  
                print(e)
                return JsonResponse({'error': str(e)}, status=500)
                
        elif category == "proxy":
            try: 
                guest_user = User.objects.get(user_id=user_id)
                post = ProxyPost.objects.get(id=post_id)
                post.participants.add(guest_user)
                post.save()
                if post.participants.count() == post.max_people:
                    post.status ="모집완료"
                post.save()
                
                room, created = ChatRoom.objects.get_or_create(
                    category=category,
                    post_id=post.id,
                    host_user=post.author,
                    guest_user=guest_user,
                    defaults={
                        'last_timestamp':now(),
                        'last_message' : "채팅을 시작해 보세요",
                    }
                )
                
                return JsonResponse({'success': True, 'created':created, 'room_id': room.id})
                
            except User.DoesNotExist:
                return redirect('home:main')  # 예외 상황 대비
            
            except Exception as e:  
                print(e)
                return JsonResponse({'error': str(e)}, status=500)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
def fetch_messages(request, room_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    try:
        room = ChatRoom.objects.get(id=room_id)
    except ChatRoom.DoesNotExist:
        return JsonResponse({'error': 'Room not found'}, status=404)

    messages = ChatMessage.objects.filter(room=room).order_by('timestamp')
    data = []
    for msg in messages:
        if user_id != msg.send_user.user_id:
            msg.is_read = True
            msg.save()
            
        data.append({
            'user_id': msg.send_user.user_id,
            'message': msg.message,
            'timestamp': msg.timestamp.strftime("%p %I:%M")
                        .replace("AM", "오전")
                        .replace("PM", "오후")
        })
        
    print(data);
    return JsonResponse({'messages': data})

def cancel_chat(request, room_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST만 허용됩니다.'}, status=405)
    
    user_id = request.session.get('user_id')
    if not user_id: # 비로그인일 경우 에러 리턴
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        print(room_id, flush=True)
        room = ChatRoom.objects.get(id=room_id)
        try: # chatting room 검색
            
            # 로그인한 사용자가 이 채팅방의 host 또는 guest 인지 확인
            if room.host_user.user_id != user_id and room.guest_user.user_id != user_id:
                return JsonResponse({'error': '접근 불가'}, status=403)
            
            if room.category in ("exchange", "sale"): # 거래중인 포스트 카테고리 
                post = Photocard.objects.get(pno=room.post_id) # 거래중인 포스트 아이디
                if post.sell_state != "후" and post.buy_state != "후" :
                    post.buyer = None # 거래자 삭제
                    post.buy_state = None # 거래 상태 삭제
                    post.save()
                    room.delete()
                    
                    return JsonResponse({'success': True, 'message': f"{post.title}의 거래가 취소되었습니다."})
                else:
                    return JsonResponse({'error': f"{post.title}의 거래를 완료해 주세요"})
            elif room.category == "companion":
                post = CompanionPost.objects.get(id=room.post_id)
                user = User.objects.get(user_id=user_id)
                post.status = "모집중"
                post.participants.remove(user)
                post.save()
                room.delete()
                
                return JsonResponse({'success': True, 'message': f"{post.title}의 거래가 취소되었습니다."})
            else:
                    return JsonResponse({'error': str(e)})

            # # 교환/판매가 아니더라도 채팅방은 삭제
            # room.delete()
            # return JsonResponse({'success': True, 'message': '채팅방이 삭제되었습니다.'})
        except ChatRoom.DoesNotExist: # 없을 경우 에러 리턴
            return JsonResponse({'error': 'Room not found'}, status=404)
        
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
def block_user(request, target_id):
    user_id = request.session.get('user_id')  # 로그인 시 저장한 user_id 세션

    if not user_id:
        return redirect('login:loginp')  # 로그인 안 되어있으면 로그인 페이지로

    try:
        user = User.objects.get(user_id=user_id) # 로그인한 사용자
        target_user = User.objects.get(user_id=target_id)
        
        body = json.loads(request.body)
        reason = body.get('reason', '')
        
        try:
            # 먼저 동일한 관계가 있는지 확인
            relation = UserRelation.objects.get(
                from_user=user,
                to_user=target_user,
                relation_type='BLOCK'
            )
            return JsonResponse({'success': True, 'message': '이미 차단된 사용자입니다.'})

        except UserRelation.DoesNotExist:
            # 없다면 새로 생성
            UserRelation.objects.create(
                from_user=user,
                to_user=target_user,
                relation_type='BLOCK',
                reason=reason
            )
            return JsonResponse({'success': True, 'message': '사용자를 차단했습니다.'})
    
    except User.DoesNotExist:
        return JsonResponse({'error': '사용자를 찾을 수 없습니다.'}, status=404)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
def change_poststate(request):
    user_id = request.session.get('user_id')  # 로그인 시 저장한 user_id 세션

    if not user_id:
        return redirect('login:loginp')  # 로그인 안 되어있으면 로그인 페이지로

    try:
        user = User.objects.get(user_id=user_id) # 로그인한 사용자
        
        body = json.loads(request.body)
        room_id = body.get('room_id', '')
        
        room = ChatRoom.objects.get(id=room_id)
        
        if room.category in ("exchange", "sale"):
            post = Photocard.objects.get(pno=room.post_id)
            if room.host_user.user_id == user.user_id:
                post.sell_state = "후"
            elif room.guest_user.user_id == user.user_id:
                post.buy_state = "후"
            post.save()
            return JsonResponse({'success': True, 'message': post.title + "의 거래가 완료되었습니다."})
            
    except User.DoesNotExist:
        return JsonResponse({'error': '사용자를 찾을 수 없습니다.'}, status=404)

        
            
    
    return redirect('login:loginp')