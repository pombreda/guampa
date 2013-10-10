'use strict';

/* Services */

angular.module('allDocumentsService', ['ngResource']).
factory('AllDocuments',
    function($resource){
      return $resource('/json/documents',
                       {},
                       {query: {method:'GET', isArray:true}});
    });

angular.module('allTagsService', ['ngResource']).
factory('AllTags',
    function($resource){
      return $resource('/json/tags',
                       {},
                       {query: {method:'GET', isArray:true}});
    });
