// A super basic inflection library to pluralize words.
var pluralize = function (word, count) {
  if (count === 1) { return word; }

  return word + 's';
};

// Add a delay before executing something to prevent hammering the server.
var typewatch = function () {
  var timer = 0;

  return function (callback, ms) {
    clearTimeout(timer);
    return timer = setTimeout(callback, ms);
  };
}();

// Format datetimes in multiple ways, depending on which CSS class is set on it.
var momentjsClasses = function () {
  var $fromNow = $('.from-now');
  var $shortDate = $('.short-date');

  $fromNow.each(function (i, e) {
    (function updateTime() {
      var time = moment($(e).data('datetime'));
      $(e).text(time.fromNow());
      $(e).attr('title', time.format('MMMM Do YYYY, h:mm:ss a Z'));
      setTimeout(updateTime, 1000);
    })();
  });

  $shortDate.each(function (i, e) {
    var time = moment($(e).data('datetime'));
    $(e).text(time.format('MMM Do YYYY'));
    $(e).attr('title', time.format('MMMM Do YYYY, h:mm:ss a Z'));
  });
};

// Bulk delete items.
var bulkDelete = function () {
  var selectAll = '#select_all';
  var checkedItems = '.checkbox-item';
  var colheader = '.col-header';
  var selectedRow = 'warning';
  var updateScope = '#scope';
  var bulkActions = '#bulk_actions';

  $('body').on('change', checkedItems, function () {
    var checkedSelector = checkedItems + ':checked';
    var itemCount = $(checkedSelector).length;
    var pluralizeItem = pluralize('item', itemCount);
    var scopeOptionText = itemCount + ' selected ' + pluralizeItem;

    if ($(this).is(':checked')) {
      $(this).closest('tr').addClass(selectedRow);

      $(colheader).hide();
      $(bulkActions).show();
    }
    else {
      $(this).closest('tr').removeClass(selectedRow);

      if (itemCount === 0) {
        $(bulkActions).hide();
        $(colheader).show();
      }
    }

    $(updateScope + ' option:first').text(scopeOptionText);
  });

  $('body').on('change', selectAll, function () {
    var checkedStatus = this.checked;

    $(checkedItems).each(function () {
      $(this).prop('checked', checkedStatus);
      $(this).trigger('change');
    });
  });
};

// Deal with displaying coupon information.
var coupons = function () {
  var durationSelector = '#duration';
  var durationInMonths = '#duration-in-months';
  var redeemBy = '#redeem_by';
  
  var $duration = $(durationSelector);
  var $durationInMonths = $(durationInMonths);
  var $redeemBy = $(redeemBy);
  
  $('body').on('change', durationSelector, function () {
    if ($duration.val() === 'repeating') {
      $durationInMonths.show();
    }
    else {
      $durationInMonths.hide();
    }
  });

  if ($redeemBy.length) {
    $redeemBy.datetimepicker({
      widgetParent: '.dt',
      format: 'YYYY-MM-DD HH:mm:ss',
      icons: {
        time: 'fa fa-clock-o',
        date: 'fa fa-calendar',
        up: 'fa fa-arrow-up',
        down: 'fa fa-arrow-down',
        previous: 'fa fa-chevron-left',
        next: 'fa fa-chevron-right',
        clear: 'fa fa-trash'
      }
    });
  }
};

// Handling processing payments with Stripe.
var stripe = function (form_id) {
  var couponCodeSelector = '#coupon_code';

  var $form = $(form_id);
  var $couponCode = $(couponCodeSelector);
  var $couponCodeStatus = $('#coupon_code_status');
  var $stripeKey = $('#stripe_key');
  var $paymentErrors = $('.payment-errors');
  var $spinner = $('.spinner');

  var errors = {
    'missing_name': 'You must enter your name.'
  };

  // This identifies your website in the createToken call below.
  if ($stripeKey.val()) {
    Stripe.setPublishableKey($stripeKey.val());
  }

  var stripeResponseHandler = function (status, response) {
    $paymentErrors.hide();

    if (response.error) {
      $spinner.hide();
      $form.find('button').prop('disabled', false);
      $paymentErrors.text(response.error.message);
      $paymentErrors.show();
    }
    else {
      // Token contains id, last 4 digits, and card type.
      var token = response.id;

      // Insert the token into the form so it gets submit to the server.
      var field = '<input type="hidden" id="stripe_token" name="stripe_token" />';
      $form.append($(field).val(token));

      // Process the payment.
      $spinner.show();
      $form.get(0).submit();
    }
  };

  var discountType = function (percentOff, amountOff) {
    if (percentOff) {
      return percentOff + '%';
    }

    return '$' + amountOff;
  };

  var discountDuration = function (duration, durationInMonths) {
    switch (duration) {
      case 'forever':
      {
        return ' forever';
      }
      case 'once':
      {
        return ' first payment';
      }
      default:
      {
        return ' for ' + durationInMonths + ' months';
      }
    }
  };

  var protectAgainstInvalidCoupon = function (coupon, couponStatus) {
    if (couponStatus.is(':visible') && 
        !couponStatus.hasClass('alert-success')) {
      coupon.select();
      return false;
    }

    return true;
  };

  var checkCouponCode = function (csrfToken) {
    return $.ajax({
      type: 'POST',
      url: '/subscription/coupon_code',
      data: {coupon_code: $(couponCodeSelector).val()},
      dataType: 'json',
      beforeSend: function (xhr) {
        xhr.setRequestHeader('X-CSRFToken', csrfToken);
        return $couponCodeStatus.text('')
          .removeClass('alert-success alert-warning alert-error').hide();
      }
    }).done(function (data, status, xhr) {
      var code = xhr.responseJSON.data;
      var amount = discountType(code.percent_off, code.amount_off) + ' off';
      var duration = discountDuration(code.duration, code.duration_in_months);

      return $couponCodeStatus.addClass('alert-success')
        .text(amount + duration);
    }).fail(function (xhr, status, error) {
      var status_class = 'alert-error';
      if (xhr.status === 404) {
        status_class = 'alert-warning';
      }

      return $couponCodeStatus.addClass(status_class)
        .text(xhr.responseJSON.error);
    }).always(function (xhr, status, error) {
      $couponCodeStatus.show();
      return $couponCode.val();
    });
  };

  jQuery(function ($) {
    var lookupDelayInMS = 300;
    var csrfToken = $('meta[name=csrf-token]').attr('content');

    $('body').on('keyup', couponCodeSelector, function () {
      if ($couponCode.val().length === 0) {
        $couponCodeStatus.hide();
        return false;
      }

      typewatch(function () {
        checkCouponCode(csrfToken);
      }, lookupDelayInMS);
    });

    $('body').on('submit', $('form').closest('button'), function () {
      if (!protectAgainstInvalidCoupon($couponCode, $couponCodeStatus)) {
        return false;
      }

      $spinner.show();
    });

    $('body').on('submit', form_id, function () {
      var $form = $(this);
      var $name = $('#name');

      if (!protectAgainstInvalidCoupon($couponCode, $couponCodeStatus)) {
        return false;
      }

      $spinner.show();
      $paymentErrors.hide();

      // Custom check to make sure their name exists.
      if ($name.val().length === 0) {
        $paymentErrors.text(errors.missing_name);
        $paymentErrors.show();
        $spinner.hide();

        return false;
      }

      // Disable the submit button to prevent repeated clicks.
      $form.find('button').prop('disabled', true);

      Stripe.card.createToken($form, stripeResponseHandler);

      // Prevent the form from submitting with the default action.
      return false;
    });
  });
};

// Placing bets.
var bets = function () {
  var guessSelector = '#guess';
  var wageredSelector = '#wagered';
  var recentBetsSelector = '#recent_bets';
  var $userCoins = $('#user_coins');
  var $outcomeStatus = $('#outcome');
  var $spinner = $('.spinner');
  var $form = $('#place_bet');
  
  var placeBet = function (csrfToken) {
    return $.ajax({
      type: 'POST',
      url: '/bet/place',
      data: {guess: $(guessSelector).val(), wagered: $(wageredSelector).val()},
      dataType: 'json',
      beforeSend: function (xhr) {
        xhr.setRequestHeader('X-CSRFToken', csrfToken);
        return $outcomeStatus.text('')
          .removeClass('alert-success alert-warning alert-error').hide();
      }
    }).done(function (data, status, xhr) {
      var parsed_data = xhr.responseJSON.data;
      var dice_entities = '';
      var status_class = '';
      var coinsLeft = parseInt($userCoins.text());

      $userCoins.text(coinsLeft + parsed_data.net);

      if (parsed_data.is_winner) {
        status_class = '<i class="fa fa-fw fa-smile-o"></i> Congrats, you won!';
        bet_class = 'success';
      } else {
        status_class = '<i class="fa fa-fw fa-frown-o"></i> You lost, try again!';
        bet_class = 'danger';
      }

      dice_entities += "&#x268" + (parseInt(parsed_data.die_1) - 1) + "; ";
      dice_entities += "&#x268" + (parseInt(parsed_data.die_2) - 1) + "; ";

      $('#dice').html(dice_entities);
      $(recentBetsSelector).show();

      var guessCol = '<td>' + parsed_data.guess + '</td>';
      var rollCol = '<td>' + parsed_data.roll + '</td>';
      var wageredCol = '<td class="text-warning"><i class="fa fa-fw fa-database"></i> ' + parsed_data.wagered + '</td>';
      var payoutCol = '<td>' + parseFloat(parsed_data.payout) + 'x</td>';
      var netCol = '<td class="text-' + bet_class + '"><i class="fa fa-fw fa-database"></i> ' + parsed_data.net + '</td>';

      var recentBet = '<tr>' + guessCol + rollCol + wageredCol + payoutCol + netCol + '</tr>';
      var recentBetCount = $(recentBetsSelector + ' tr').length;

      $(recentBetsSelector + ' tbody').prepend(recentBet);
      if (recentBetCount > 10) {
        $(recentBetsSelector + ' tr:last').remove();
      }

      return $outcomeStatus.addClass('alert alert-info alert-small').html(status_class);
    }).fail(function (xhr, status, error) {
      var status_class = 'alert-error';
      var error_status = 'You are out of coins. You should buy more.';

      if (xhr.responseJSON) {
        error_status = xhr.responseJSON.error;
      } else if (error == 'TOO MANY REQUESTS') {
        error_status = 'You have been temporarily rate limited.';
      }

      return $outcomeStatus.addClass(status_class).text(error_status);
    }).always(function (xhr, status, error) {
      $spinner.hide();
      $form.find('button').prop('disabled', false);

      $outcomeStatus.show();
      return xhr;
    });
  };

  jQuery(function ($) {
    var csrfToken = $('meta[name=csrf-token]').attr('content');

    $('body').on('submit', '#place_bet', function () {
      $spinner.show();
      $form.find('button').prop('disabled', true);

      placeBet(csrfToken);

      return false;
    });
  });
};

// Initialize everything when the browser is ready.
$(document).ready(function() {
  momentjsClasses();
  bulkDelete();
  coupons();
  stripe('#subscription_form');
  stripe('#payment_form');
  bets();
});

