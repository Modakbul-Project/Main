                   //마우스 가로 스크롤 이벤트
                $(function() {

                    $(".cards").mousewheel(function(event, delta) {

                        this.scrollLeft -= (delta * 30);

                        event.preventDefault();

                    });
                $('.cards').scroll(function() {
                    if ($(this).scrollLeft() <= 1) {
                        $(this).siblings(".scrollBt-left").fadeOut();
                    } else if($(this).scrollLeft() >= ($(this).children().width() - $(this).width() - 1)) {
                        $(this).siblings(".scrollBt-right").fadeOut();
                    }else{
                        $(this).siblings(".scrollBt-left").fadeIn();
                        $(this).siblings(".scrollBt-right").fadeIn();
                    };
                });

                });
               //스크롤 버튼
                $(".scrollBt-right").click(function(){
                    $(this).siblings(".cards").animate({scrollLeft:"+=500"},800);
                });
                $(".scrollBt-left").click(function(){
                    $(this).siblings(".cards").animate({scrollLeft:"-=500"},800);
                });

